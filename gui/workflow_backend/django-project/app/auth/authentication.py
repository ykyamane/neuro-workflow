import jwt
import requests
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Supabase JWT Authentication class
    """

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()

        if not auth_header or auth_header[0].lower() != b"bearer":
            return None

        if len(auth_header) == 1:
            msg = "Invalid token header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = "Invalid token header. Token string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth_header[1].decode("utf-8")
        except UnicodeError:
            msg = "Invalid token header. Token string should not contain invalid characters."
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        """
        Supabase JWTValidate the token and get or create the user
        """
        try:
            # Get the Supabase public key and validate the token
            payload = self.verify_token(token)

            # Get user information
            user_id = payload.get("sub")
            email = payload.get("email")

            if not user_id or not email:
                raise exceptions.AuthenticationFailed("Invalid token payload.")

            # Get or create a Django user
            user = self.get_or_create_user(user_id, email, payload)

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed("Authentication failed.")

    def verify_token(self, token):
        """
        SupValidate JWT token in Supabase
        """
        # SupabaIt should be taken from your Supabase project settings
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_ANON_KEY

        # Obtained from the JWT header kid (key id) 
        unverified_header = jwt.get_unverified_header(token)

        # Get the Supabase public key
        jwks_url = f"{supabase_url}/auth/v1/jwks"
        jwks_response = requests.get(jwks_url)
        jwks = jwks_response.json()

        # Finding the right public key
        public_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header.get("kid"):
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not public_key:
            raise jwt.InvalidTokenError("Unable to find appropriate key")

        # Validate token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1",
        )

        return payload

    def get_or_create_user(self, user_id, email, payload):
        """
        Get or create Django users from Supabase user information
        """
        User = get_user_model()

        # First, Search by Supabase UID
        try:
            user = User.objects.get(username=user_id)
            return user
        except User.DoesNotExist:
            pass

        # Next, Search by mail address
        try:
            user = User.objects.get(email=email)
            # Update username to Supabase UID
            user.username = user_id
            user.save()
            return user
        except User.DoesNotExist:
            pass

        # Create new user
        user = User.objects.create_user(
            username=user_id,
            email=email,
            first_name=payload.get("user_metadata", {}).get("first_name", ""),
            last_name=payload.get("user_metadata", {}).get("last_name", ""),
        )

        return user


# settings.py
"""
SUPABASE_URL = 'https://your-project.supabase.co'
SUPABASE_ANON_KEY = 'your-anon-key'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'your_app.authentication.SupabaseAuthentication',
        # Add other authentication classes as needed
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS設定
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Also added the production frontend URL
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
"""

# views.py
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({
        'message': 'Hello authenticated user!',
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'date_joined': request.user.date_joined,
        }
    })
"""
