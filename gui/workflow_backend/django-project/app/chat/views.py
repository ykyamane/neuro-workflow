import asyncio
import json
import logging

from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    SendMessageSerializer,
)
from .services.chat_orchestrator import orchestrate_chat

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ConversationListCreateView(APIView):
    """List and create conversations."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        conversations = Conversation.objects.filter(is_active=True)
        serializer = ConversationListSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save()
            return Response(
                ConversationSerializer(conversation).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class ConversationDetailView(APIView):
    """Retrieve or delete a conversation."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                id=conversation_id, is_active=True,
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

    def delete(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
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

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get("conversation_id")
        project_id = serializer.validated_data.get("project_id")

        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id, is_active=True,
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
                    logger.error(f"Stream error: {e}", exc_info=True)
                    yield _format_sse("error", {"message": str(e)})
                    break
        finally:
            loop.close()


def _format_sse(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
