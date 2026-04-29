import { VStack, Box, Spinner, Text } from "@chakra-ui/react";
import { useEffect, useRef } from "react";
import ChatMessageBubble from "./ChatMessageBubble";
import ToolCallDisplay from "./ToolCallDisplay";
import useChatStore from "@/stores/chatStore";
import type { ChatMessage, ActiveToolCall } from "@/stores/chatStore";

const ChatMessageList: React.FC = () => {
  const messages = useChatStore((s) => s.messages);
  const activeToolCalls = useChatStore((s) => s.activeToolCalls);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Scroll within our container only — never propagate to ancestors
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, activeToolCalls]);

  // Build display items: messages interleaved with tool calls
  const displayItems: Array<
    | { type: "message"; data: ChatMessage }
    | { type: "tool_call"; data: ActiveToolCall }
  > = [];

  let toolCallIdx = 0;
  for (const msg of messages) {
    displayItems.push({ type: "message", data: msg });

    // After an assistant message with tool_calls, show the tool call displays
    if (msg.role === "assistant" && msg.tool_calls) {
      for (const tc of msg.tool_calls) {
        const activeTc = activeToolCalls.find(
          (a) => a.tool_call_id === tc.id
        );
        if (activeTc) {
          displayItems.push({ type: "tool_call", data: activeTc });
          toolCallIdx++;
        }
      }
    }
  }

  // Show any remaining active tool calls not yet matched to messages
  for (let i = toolCallIdx; i < activeToolCalls.length; i++) {
    const tc = activeToolCalls[i];
    const alreadyShown = displayItems.some(
      (item) =>
        item.type === "tool_call" && item.data.tool_call_id === tc.tool_call_id
    );
    if (!alreadyShown) {
      displayItems.push({ type: "tool_call", data: tc });
    }
  }

  return (
    <Box ref={scrollContainerRef} flex={1} minH={0} overflowY="auto" px={2} py={2}>
      <VStack spacing={2} align="stretch">
        {displayItems.length === 0 && !isStreaming && (
          <Box textAlign="center" py={8}>
            <Text color="gray.500" fontSize="sm">
              Start a conversation with AI Assistant
            </Text>
          </Box>
        )}

        {displayItems.map((item, idx) =>
          item.type === "message" ? (
            <ChatMessageBubble key={item.data.id || idx} message={item.data} />
          ) : (
            <ToolCallDisplay
              key={item.data.tool_call_id || idx}
              toolCall={item.data}
            />
          )
        )}

        {isStreaming &&
          messages.length > 0 &&
          messages[messages.length - 1].role !== "assistant" && (
            <Box pl={2}>
              <Spinner size="sm" color="blue.300" />
            </Box>
          )}

      </VStack>
    </Box>
  );
};

export default ChatMessageList;
