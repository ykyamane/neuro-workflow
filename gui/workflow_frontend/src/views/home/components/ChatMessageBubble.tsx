import { Box, Text, Flex } from "@chakra-ui/react";
import type { ChatMessage } from "@/stores/chatStore";

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({ message }) => {
  if (message.role === "system") return null;
  if (message.role === "tool") return null; // Tool results are shown via ToolCallDisplay

  const isUser = message.role === "user";

  return (
    <Flex justify={isUser ? "flex-end" : "flex-start"} w="100%">
      <Box
        maxW="85%"
        bg={isUser ? "blue.600" : "gray.700"}
        color="white"
        px={3}
        py={2}
        borderRadius="lg"
        borderTopRightRadius={isUser ? "sm" : "lg"}
        borderTopLeftRadius={isUser ? "lg" : "sm"}
        fontSize="sm"
        whiteSpace="pre-wrap"
        wordBreak="break-word"
      >
        <Text>{message.content}</Text>
      </Box>
    </Flex>
  );
};

export default ChatMessageBubble;
