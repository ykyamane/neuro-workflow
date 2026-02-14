import { create } from "zustand";

// Types

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "tool" | "system";
  content: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  tool_name?: string;
  created_at?: string;
}

export interface ToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
}

export interface ActiveToolCall {
  tool_call_id: string;
  tool_name: string;
  arguments: string;
  result?: string;
  status: "running" | "done" | "error";
}

export interface ConversationSummary {
  id: string;
  title: string;
  project: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ChatStore {
  // Conversations
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  setConversations: (conversations: ConversationSummary[]) => void;
  setActiveConversationId: (id: string | null) => void;

  // Messages
  messages: ChatMessage[];
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  updateLastAssistantMessage: (contentDelta: string) => void;

  // Streaming
  isStreaming: boolean;
  setIsStreaming: (isStreaming: boolean) => void;
  abortController: AbortController | null;
  setAbortController: (controller: AbortController | null) => void;

  // Tool calls
  activeToolCalls: ActiveToolCall[];
  addToolCall: (toolCall: ActiveToolCall) => void;
  updateToolCallArgs: (content: string) => void;
  updateToolCallResult: (
    toolCallId: string,
    result: string,
    status: "done" | "error"
  ) => void;
  clearToolCalls: () => void;

  // Error
  error: string | null;
  setError: (error: string | null) => void;

  // Reset
  resetChat: () => void;
}

const useChatStore = create<ChatStore>((set) => ({
  // Conversations
  conversations: [],
  activeConversationId: null,
  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (id) => set({ activeConversationId: id }),

  // Messages
  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  updateLastAssistantMessage: (contentDelta) =>
    set((state) => {
      const msgs = [...state.messages];
      const lastIdx = msgs.length - 1;
      if (lastIdx >= 0 && msgs[lastIdx].role === "assistant") {
        msgs[lastIdx] = {
          ...msgs[lastIdx],
          content: msgs[lastIdx].content + contentDelta,
        };
      } else {
        // Create new assistant message for streaming
        msgs.push({
          id: `streaming-${Date.now()}`,
          role: "assistant",
          content: contentDelta,
        });
      }
      return { messages: msgs };
    }),

  // Streaming
  isStreaming: false,
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  abortController: null,
  setAbortController: (controller) => set({ abortController: controller }),

  // Tool calls
  activeToolCalls: [],
  addToolCall: (toolCall) =>
    set((state) => ({
      activeToolCalls: [...state.activeToolCalls, toolCall],
    })),
  updateToolCallArgs: (content) =>
    set((state) => {
      const calls = [...state.activeToolCalls];
      if (calls.length > 0) {
        const last = calls[calls.length - 1];
        calls[calls.length - 1] = {
          ...last,
          arguments: last.arguments + content,
        };
      }
      return { activeToolCalls: calls };
    }),
  updateToolCallResult: (toolCallId, result, resultStatus) =>
    set((state) => ({
      activeToolCalls: state.activeToolCalls.map((tc) =>
        tc.tool_call_id === toolCallId
          ? { ...tc, result, status: resultStatus }
          : tc
      ),
    })),
  clearToolCalls: () => set({ activeToolCalls: [] }),

  // Error
  error: null,
  setError: (error) => set({ error }),

  // Reset
  resetChat: () =>
    set({
      messages: [],
      activeConversationId: null,
      activeToolCalls: [],
      isStreaming: false,
      abortController: null,
      error: null,
    }),
}));

export default useChatStore;
