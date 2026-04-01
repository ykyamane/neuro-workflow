import { createAuthHeaders } from "./authHeaders";

const API_PREFIX = "/api";

export interface WorkflowRunSSEEvent {
  type: string;
  data: Record<string, unknown>;
}

/**
 * Start a workflow run via SSE streaming.
 *
 * The backend will execute the generated Python script on a Jupyter kernel
 * and stream stdout/stderr/errors back as Server-Sent Events.
 */
export const runWorkflowStream = async (
  workflowId: string,
  onEvent: (event: WorkflowRunSSEEvent) => void,
  signal?: AbortSignal
) => {
  const headers = await createAuthHeaders();

  const res = await fetch(`${API_PREFIX}/workflow/${workflowId}/run/`, {
    method: "POST",
    headers,
    signal,
  });

  if (!res.ok) {
    const body = await res.text();
    let errorMsg: string;
    try {
      const parsed = JSON.parse(body);
      errorMsg = parsed.error || body;
    } catch {
      errorMsg = body;
    }
    throw new Error(`Workflow run error ${res.status}: ${errorMsg}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEventType = "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEventType = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const dataStr = line.slice(6);
        try {
          const data = JSON.parse(dataStr);
          onEvent({ type: currentEventType, data });
        } catch (e) {
          console.warn("[workflowRunApi] Failed to parse SSE data:", dataStr, e);
        }
        currentEventType = "";
      }
    }
  }
};
