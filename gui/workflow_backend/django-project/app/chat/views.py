import asyncio
import json
import logging

from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import exceptions as drf_exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app.auth.authentication import KeycloakAuthentication, SupabaseAuthentication

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    SendMessageSerializer,
)
from .services.chat_orchestrator import orchestrate_chat

logger = logging.getLogger(__name__)


class _OptionalAuthentication(KeycloakAuthentication):
    """Try Keycloak first, then Supabase; return None on any failure.

    Chat views use AllowAny with anonymous fallback, so authentication
    errors should be silently ignored rather than blocking the request.
    """

    _supabase = SupabaseAuthentication()

    def authenticate(self, request):
        for backend in (super(), self._supabase):
            try:
                result = backend.authenticate(request)
                if result:
                    logger.info("Chat auth succeeded for user: %s", result[0])
                    return result
            except drf_exceptions.AuthenticationFailed:
                continue
            except Exception as e:
                logger.warning("Chat auth error (skipping): %s", e)
                continue
        return None


def _get_user(request):
    """Return the authenticated user, or fall back to a per-session anonymous user."""
    if request.user and request.user.is_authenticated:
        return request.user
    # Ensure a session exists so each anonymous visitor gets isolated data.
    if not request.session.session_key:
        request.session.create()
    anonymous_username = f"anonymous_{request.session.session_key}"
    user, _ = User.objects.get_or_create(
        username=anonymous_username,
        defaults={"email": "", "is_active": True},
    )
    return user


@method_decorator(csrf_exempt, name="dispatch")
class ConversationListCreateView(APIView):
    """List and create conversations."""

    authentication_classes = [_OptionalAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        user = _get_user(request)
        conversations = Conversation.objects.filter(user=user, is_active=True)
        serializer = ConversationListSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = _get_user(request)
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save(user=user)
            return Response(
                ConversationSerializer(conversation).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class ConversationDetailView(APIView):
    """Retrieve or delete a conversation."""

    authentication_classes = [_OptionalAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, conversation_id):
        user = _get_user(request)
        try:
            conversation = Conversation.objects.get(
                id=conversation_id, user=user, is_active=True,
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

    def delete(self, request, conversation_id):
        user = _get_user(request)
        try:
            conversation = Conversation.objects.get(
                id=conversation_id, user=user,
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        conversation.is_active = False
        conversation.save()
        return Response({"status": "deleted"}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class ChatStreamView(APIView):
    """Handle chat messages with SSE streaming response."""

    authentication_classes = [_OptionalAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = _get_user(request)
        user_message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get("conversation_id")
        project_id = serializer.validated_data.get("project_id")

        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id, user=user, is_active=True,
                )
            except Conversation.DoesNotExist:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Create new conversation
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            conversation = Conversation.objects.create(
                title=title,
                user=user,
                project_id=project_id,
            )

        response = StreamingHttpResponse(
            self._sync_event_generator(conversation, user_message),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        response["X-Conversation-Id"] = str(conversation.id)
        return response

    def _sync_event_generator(self, conversation, user_message):
        """Wrap the async orchestrator into a sync generator for WSGI."""
        loop = asyncio.new_event_loop()

        try:
            # Send the conversation ID as the first event
            yield _format_sse("conversation_id", {"id": str(conversation.id)})

            agen = orchestrate_chat(conversation, user_message)

            while True:
                try:
                    event = loop.run_until_complete(agen.__anext__())
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    yield _format_sse(event_type, event_data)
                except StopAsyncIteration:
                    break
                except Exception as e:
                    logger.error("Stream error: %s", e, exc_info=True)
                    yield _format_sse("error", {"message": str(e)})
                    break
        finally:
            loop.close()


def _format_sse(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
