import jwt
import logging
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class SupabaseAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Supabase public key (JWKS URL or public key)
        # Actually obtained from environment variables or settings.py
        self.supabase_public_key = settings.SUPABASE_PUBLIC_KEY

    def __call__(self, request):
        # Disable CSRF check for API paths
        if request.path.startswith("/api/"):
            setattr(request, "_dont_enforce_csrf_checks", True)

        if self._is_public_path(request.path):
            return self.get_response(request)

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return self.get_response(request)

        token = auth_header.replace("Bearer ", "")

        try:
            payload = jwt.decode(
                token,
                self.supabase_public_key,
                algorithms=["RS256"],
                options={"verify_signature": True},
            )

            user_id = payload.get("sub")
            request.supabase_user_id = user_id

            logger.info(f"Authentication successful: User ID {user_id}")

        except jwt.ExpiredSignatureError:
            logger.warning("expired token")
            request.token_error = "expired"

        except jwt.InvalidTokenError:
            logger.warning("invalid token")
            request.token_error = "invalid"

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            request.token_error = "error"

        return self.get_response(request)

    def _is_public_path(self, path):
        """Check if path is publicly accessible (optional)"""
        public_paths = [
            "/api/public/",
            "/api/docs/",
            "/api/workflow/sample-flow/",
        ]
        return any(path.startswith(prefix) for prefix in public_paths)


# def supabase_auth_required(view_func):
#     from functools import wraps

#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         # If there is a token error
#         if hasattr(request, "token_error"):
#             error_messages = {
#                 "expired": "Token has expired",
#                 "invalid": "Invalid token",
#                 "error": "Authentication error",
#             }
#             message = error_messages.get(request.token_error, "Authentication required")
#             return JsonResponse({"error": message}, status=401)

#         # If you have a token but no user ID
#         if not hasattr(request, "supabase_user_id") or not request.supabase_user_id:
#             return JsonResponse({"error": "Authentication required"}, status=401)

#         return view_func(request, *args, **kwargs)

#     return wrapper
