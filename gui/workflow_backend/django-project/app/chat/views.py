import asyncio
import json
import logging

from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import authentication, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.auth.authentication import KeycloakAuthentication, ServiceTokenAuthentication

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    SendMessageSerializer,
)
from .services.chat_orchestrator import orchestrate_chat
from .services.mcp_client import MCPClient, mcp_tools_to_openai_functions
from .services.openai_client import stream_chat_completion

logger = logging.getLogger(__name__)


def _extract_bearer_token(request) -> str | None:
    """Extract the bearer token from the Authorization header so it can be
    forwarded to the MCP server (and onward to the Django API)."""
    parts = authentication.get_authorization_header(request).split()
    if len(parts) == 2 and parts[0].lower() == b"bearer":
        try:
            return parts[1].decode("utf-8")
        except UnicodeError:
            return None
    return None


@method_decorator(csrf_exempt, name="dispatch")
class ConversationListCreateView(APIView):
    """List and create conversations."""

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(user=request.user, is_active=True)
        serializer = ConversationListSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save(user=request.user)
            return Response(
                ConversationSerializer(conversation).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class ConversationDetailView(APIView):
    """Retrieve or delete a conversation."""

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                id=conversation_id, user=request.user, is_active=True,
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
            conversation = Conversation.objects.get(
                id=conversation_id, user=request.user,
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

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        auth_token = _extract_bearer_token(request)
        user_message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get("conversation_id")
        project_id = serializer.validated_data.get("project_id")

        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id, user=user, is_active=True,
                )
                # Update project context if the active project changed
                if project_id and str(conversation.project_id) != str(project_id):
                    conversation.project_id = project_id
                    conversation.save(update_fields=["project_id"])
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
            self._sync_event_generator(conversation, user_message, auth_token),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        response["X-Conversation-Id"] = str(conversation.id)
        return response

    def _sync_event_generator(self, conversation, user_message, auth_token):
        """Wrap the async orchestrator into a sync generator for WSGI."""
        loop = asyncio.new_event_loop()

        try:
            # Send the conversation ID as the first event
            yield _format_sse("conversation_id", {"id": str(conversation.id)})

            agen = orchestrate_chat(conversation, user_message, auth_token=auth_token)

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


@method_decorator(csrf_exempt, name="dispatch")
class NotebookLLMView(APIView):
    """Stateless OpenAI streaming proxy for the in-notebook chat agent.

    The agent loop runs inside the Jupyter kernel and keeps its own
    conversation state, so this endpoint persists nothing: it relays one
    ``stream_chat_completion`` pass (the kernel handles tool dispatch and
    re-calls this endpoint with updated messages). It also keeps the OpenAI
    key on the backend rather than exposing it inside user-accessible kernels.
    """

    authentication_classes = [ServiceTokenAuthentication, KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        messages = request.data.get("messages")
        if not isinstance(messages, list) or not messages:
            return Response(
                {"error": "'messages' must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tools = request.data.get("tools") or None

        response = StreamingHttpResponse(
            self._sync_stream(messages, tools),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def _sync_stream(self, messages, tools):
        loop = asyncio.new_event_loop()
        try:
            agen = stream_chat_completion(messages, tools)
            while True:
                try:
                    chunk = loop.run_until_complete(agen.__anext__())
                    chunk_type = chunk.pop("type", "unknown")
                    yield _format_sse(chunk_type, chunk)
                except StopAsyncIteration:
                    break
                except Exception as e:
                    logger.error("LLM proxy stream error: %s", e, exc_info=True)
                    yield _format_sse("error", {"message": str(e)})
                    break
        finally:
            loop.close()


@method_decorator(csrf_exempt, name="dispatch")
class NotebookMCPToolsView(APIView):
    """List MCP workflow tools (OpenAI function format) for the notebook agent.

    Requires a real Keycloak JWT: the same token is forwarded to the MCP server
    so per-user workflow data is scoped correctly. The service token is not
    accepted here because it carries no end-user identity.
    """

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = _extract_bearer_token(request)

        async def _run():
            mcp = MCPClient(auth_token=token)
            await mcp.initialize()
            tools = await mcp.list_tools()
            return mcp_tools_to_openai_functions(tools)

        try:
            tools = asyncio.run(_run())
        except Exception as e:
            logger.error("mcp-tools error: %s", e, exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY
            )
        return Response({"tools": tools})


@method_decorator(csrf_exempt, name="dispatch")
class NotebookMCPCallView(APIView):
    """Execute a single MCP workflow tool on behalf of the notebook agent."""

    authentication_classes = [KeycloakAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tool_name = request.data.get("tool_name")
        arguments = request.data.get("arguments") or {}
        if not tool_name:
            return Response(
                {"error": "'tool_name' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(arguments, dict):
            return Response(
                {"error": "'arguments' must be an object"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = _extract_bearer_token(request)

        async def _run():
            mcp = MCPClient(auth_token=token)
            await mcp.initialize()
            return await mcp.call_tool(tool_name, arguments)

        try:
            result = asyncio.run(_run())
        except Exception as e:
            logger.error("mcp-call error: %s", e, exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY
            )
        return Response({"result": result})
