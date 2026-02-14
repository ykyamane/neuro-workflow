import httpx
import json
import logging
import os

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


async def stream_chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
):
    """Stream a chat completion from the OpenAI API.

    Yields parsed SSE chunks as dicts. Each chunk has a "type" field:
      - "content_delta": partial text content
      - "tool_call_delta": partial tool call data
      - "done": stream finished
      - "error": an error occurred
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "stream": True,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", OPENAI_API_URL, json=payload, headers=headers,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield {"type": "error", "message": f"OpenAI API error {response.status_code}: {body.decode()}"}
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        yield {"type": "done"}
                        return

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason")

                    # Text content delta
                    if delta.get("content"):
                        yield {"type": "content_delta", "content": delta["content"]}

                    # Tool call deltas
                    if delta.get("tool_calls"):
                        for tc in delta["tool_calls"]:
                            yield {
                                "type": "tool_call_delta",
                                "index": tc.get("index", 0),
                                "id": tc.get("id"),
                                "function_name": tc.get("function", {}).get("name"),
                                "arguments_delta": tc.get("function", {}).get("arguments", ""),
                            }

                    if finish_reason == "stop":
                        yield {"type": "done"}
                        return
                    elif finish_reason == "tool_calls":
                        yield {"type": "tool_calls_complete"}
                        return

    except httpx.HTTPError as e:
        logger.error(f"OpenAI HTTP error: {e}")
        yield {"type": "error", "message": f"OpenAI connection error: {str(e)}"}
    except Exception as e:
        logger.error(f"OpenAI unexpected error: {e}", exc_info=True)
        yield {"type": "error", "message": f"Unexpected error: {str(e)}"}
