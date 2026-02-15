import json
import logging

from asgiref.sync import sync_to_async

from ..models import Conversation, Message
from .mcp_client import MCPClient, mcp_tools_to_openai_functions
from .openai_client import stream_chat_completion

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant for NeuroWorkflow, a visual workflow editor. "
    "You can help users manage their workflow projects, nodes, and edges using the available tools. "
    "When a user asks to view, create, modify, or delete workflow elements, use the appropriate tools. "
    "Always respond in the same language the user uses. "
    "Be concise and helpful."
)

MAX_AGENT_LOOPS = 10


@sync_to_async
def _create_message(**kwargs):
    return Message.objects.create(**kwargs)


@sync_to_async
def _build_openai_messages(conversation: Conversation) -> list[dict]:
    """Build the OpenAI messages array from conversation history."""
    messages = []

    # System prompt
    system_prompt = conversation.system_prompt or DEFAULT_SYSTEM_PROMPT
    messages.append({"role": "system", "content": system_prompt})

    # History
    for msg in conversation.messages.all():
        messages.append(msg.to_openai_format())

    return messages


async def orchestrate_chat(conversation: Conversation, user_message: str):
    """Run the agent loop: LLM -> tool calls -> LLM -> ... -> final response.

    This is an async generator that yields SSE event dicts.
    """
    # 1. Save user message
    await _create_message(
        conversation=conversation,
        role="user",
        content=user_message,
    )

    # 2. Initialize MCP client and get tools
    mcp = MCPClient()
    try:
        await mcp.initialize()
    except Exception as e:
        logger.warning("MCP initialize failed (may already be initialized): %s", e)

    try:
        mcp_tools = await mcp.list_tools()
        openai_tools = mcp_tools_to_openai_functions(mcp_tools)
    except Exception as e:
        logger.error("Failed to get MCP tools: %s", e)
        openai_tools = []

    # 3. Agent loop
    for loop_idx in range(MAX_AGENT_LOOPS):
        # Build message history for OpenAI
        messages = await _build_openai_messages(conversation)

        # Stream OpenAI response
        full_content = ""
        tool_calls_map = {}  # index -> {id, name, arguments}

        async for chunk in stream_chat_completion(messages, openai_tools or None):
            if chunk["type"] == "content_delta":
                full_content += chunk["content"]
                yield {
                    "type": "text_delta",
                    "data": {"content": chunk["content"]},
                }

            elif chunk["type"] == "tool_call_delta":
                idx = chunk["index"]
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {
                        "id": chunk.get("id", ""),
                        "name": chunk.get("function_name", ""),
                        "arguments": "",
                    }
                tc = tool_calls_map[idx]
                if chunk.get("id"):
                    tc["id"] = chunk["id"]
                if chunk.get("function_name"):
                    tc["name"] = chunk["function_name"]
                    yield {
                        "type": "tool_call_start",
                        "data": {
                            "tool_name": tc["name"],
                            "tool_call_id": tc["id"],
                        },
                    }
                if chunk.get("arguments_delta"):
                    tc["arguments"] += chunk["arguments_delta"]
                    yield {
                        "type": "tool_call_args_delta",
                        "data": {"content": chunk["arguments_delta"]},
                    }

            elif chunk["type"] == "error":
                yield {"type": "error", "data": {"message": chunk["message"]}}
                return

            elif chunk["type"] in ("done", "tool_calls_complete"):
                break

        # Save assistant message
        if tool_calls_map:
            openai_tool_calls = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                openai_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    },
                })

            await _create_message(
                conversation=conversation,
                role="assistant",
                content=full_content,
                tool_calls=openai_tool_calls,
            )

            # Execute each tool call via MCP
            for tc_data in openai_tool_calls:
                tool_name = tc_data["function"]["name"]
                tool_call_id = tc_data["id"]
                try:
                    arguments = json.loads(tc_data["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}

                try:
                    result = await mcp.call_tool(tool_name, arguments)
                except Exception as e:
                    result = f"Error executing tool: {str(e)}"
                    logger.error("MCP tool call error for %s: %s", tool_name, e)

                # Save tool result message
                await _create_message(
                    conversation=conversation,
                    role="tool",
                    content=result,
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                )

                yield {
                    "type": "tool_result",
                    "data": {
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "result": result,
                    },
                }

            # Continue the loop — LLM will process tool results
            continue

        else:
            # No tool calls — final text response
            if full_content:
                await _create_message(
                    conversation=conversation,
                    role="assistant",
                    content=full_content,
                )
            yield {"type": "done", "data": {}}
            return

    # Max loops reached
    yield {"type": "done", "data": {}}
