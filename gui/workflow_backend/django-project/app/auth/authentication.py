import jwt
import requests
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_jwks_cache: dict = {}


def _fetch_jwks(jwks_url: str) -> list:
    """Fetch and cache JWKS keys from a remote endpoint."""
    cached = _jwks_cache.get(jwks_url)
    if cached:
        return cached
    try:
        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
    except Exception as e:
        raise jwt.InvalidTokenError(f"Failed to fetch JWKS from {jwks_url}: {e}")
    if keys:
        _jwks_cache[jwks_url] = keys
    return keys


def _verify_rs256(token: str, jwks_url: str, **decode_kwargs) -> dict:
    """Verify a JWT using RS256 against a JWKS endpoint."""
    keys = _fetch_jwks(jwks_url)
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    public_key = None
    for key in keys:
        if key.get("kid") == kid:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            break
    if not public_key:
        _jwks_cache.pop(jwks_url, None)
        keys = _fetch_jwks(jwks_url)
        for key in keys:
            if key.get("kid") == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break
    if not public_key:
        raise jwt.InvalidTokenError("No matching key found in JWKS")
    return jwt.decode(token, public_key, algorithms=["RS256"], **decode_kwargs)


def _verify_keycloak_client(payload: dict, expected_client: str | None) -> None:
    """Validate that a Keycloak token was issued for this frontend client.

    Keycloak access tokens commonly use ``azp`` (authorized party) for the SPA
    client and reserve ``aud`` for resource audiences such as ``account``. PyJWT's
    built-in audience check is therefore too strict for tokens produced by
    keycloak-js. Accept either ``azp`` or ``aud`` matching the configured client.
    """
    if not expected_client:
        return

    token_audience = payload.get("aud", [])
    if isinstance(token_audience, str):
        audiences = {token_audience}
    else:
        audiences = set(token_audience or [])

    if payload.get("azp") == expected_client or expected_client in audiences:
        return

    raise jwt.InvalidTokenError(
        f"Token was not issued for client '{expected_client}'"
    )


def _get_or_create_user(user_id: str, email: str, extra: dict | None = None):
    """Get-or-create a Django User from an external identity provider.

    Falls back to email-based lookup so users originally provisioned by a
    different IdP (e.g. legacy Supabase records) get re-bound to the new
    ``sub`` on first login.
    """
    if not user_id:
        raise exceptions.AuthenticationFailed("Invalid token payload: missing user identifier.")

    User = get_user_model()
    extra = extra or {}

    try:
        return User.objects.get(username=user_id)
    except User.DoesNotExist:
        pass

    if email:
        # Pick the oldest user with this email. Multiple rows can occur when an
        # account exists from a previous IdP and a new one was created before
        # the rebind succeeded; prefer the original to preserve owned records.
        candidates = User.objects.filter(email=email).order_by("pk")
        count = candidates.count()
        if count > 1:
            logger.warning(
                "Multiple users share email %s (ids=%s). Re-binding the oldest "
                "to sub=%s; consider deduplicating the rest.",
                email, list(candidates.values_list("pk", flat=True)), user_id,
            )
        user = candidates.first()
        if user is not None:
            user.username = user_id
            user.save(update_fields=["username"])
            return user

    return User.objects.create_user(
        username=user_id,
        email=email or "",
        first_name=extra.get("first_name", ""),
        last_name=extra.get("last_name", ""),
    )


# ---------------------------------------------------------------------------
# Base bearer-token authenticator
# ---------------------------------------------------------------------------

class _BearerAuthentication(authentication.BaseAuthentication):
    """Extract a Bearer token from the Authorization header."""

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header or auth_header[0].lower() != b"bearer":
            return None
        if len(auth_header) != 2:
            raise exceptions.AuthenticationFailed("Malformed Authorization header.")
        try:
            token = auth_header[1].decode("utf-8")
        except UnicodeError:
            raise exceptions.AuthenticationFailed("Invalid characters in token.")
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        raise NotImplementedError

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


# ---------------------------------------------------------------------------
# Keycloak OIDC authentication
# ---------------------------------------------------------------------------

class KeycloakAuthentication(_BearerAuthentication):
    """Verify JWTs issued by a Keycloak realm (RS256 via JWKS)."""

    def authenticate_credentials(self, token):
        kc_url = getattr(settings, "KEYCLOAK_URL", None)
        kc_realm = getattr(settings, "KEYCLOAK_REALM", None)
        if not kc_url or not kc_realm:
            return None

        jwks_url = f"{kc_url}/realms/{kc_realm}/protocol/openid-connect/certs"
        # Issuer in the JWT is set from the URL the *browser* used to obtain
        # the token. In split deployments (browser hits a public URL, backend
        # hits an internal hostname) this differs from KEYCLOAK_URL. Allow an
        # explicit override.
        issuer = (
            getattr(settings, "KEYCLOAK_ISSUER", None)
            or f"{kc_url}/realms/{kc_realm}"
        )
        kc_client = getattr(settings, "KEYCLOAK_CLIENT_ID", None)

        decode_kwargs: dict = {
            "issuer": issuer,
            "options": {"verify_aud": False},
        }

        try:
            payload = _verify_rs256(token, jwks_url, **decode_kwargs)
            _verify_keycloak_client(payload, kc_client)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {e}")

        sub = (
            payload.get("sub")
            or payload.get("preferred_username")
            or payload.get("email")
        )
        email = payload.get("email", "")
        user = _get_or_create_user(
            user_id=sub,
            email=email,
            extra={
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
            },
        )
        return (user, token)
