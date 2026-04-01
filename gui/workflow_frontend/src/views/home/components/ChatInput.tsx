import { Box, IconButton, Textarea, HStack, useColorModeValue } from "@chakra-ui/react";
import { useState, useRef, useCallback } from "react";
import { FiSend, FiSquare } from "react-icons/fi";

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onStop,
  isStreaming,
  disabled = false,
}) => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const composingRef = useRef(false);

  const borderColor = useColorModeValue('#e5e5e5', 'gray.600');
  const inputBg = useColorModeValue('white', 'gray.700');
  const inputBorder = useColorModeValue('#e5e5e5', 'gray.600');
  const textColor = useColorModeValue('#1a1a1a', 'white');
  const subtextColor = useColorModeValue('gray.500', 'gray.400');

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setInput("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, isStreaming, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // IME 変換中の Enter は無視する
    if (e.nativeEvent.isComposing || composingRef.current) return;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <Box p={2} borderTop="1px solid" borderColor={borderColor}>
      <HStack spacing={2} align="end">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onCompositionStart={() => { composingRef.current = true; }}
          onCompositionEnd={() => { composingRef.current = false; }}
          placeholder="Type a message..."
          bg={inputBg}
          border="1px solid"
          borderColor={inputBorder}
          color={textColor}
          resize="none"
          rows={2}
          minH="56px"
          maxH="200px"
          _placeholder={{ color: subtextColor }}
          _focus={{ borderColor: "blue.400", boxShadow: "none" }}
          disabled={disabled}
          fontSize="sm"
        />
        {isStreaming ? (
          <IconButton
            icon={<FiSquare />}
            onClick={onStop}
            aria-label="Stop generation"
            colorScheme="red"
            size="sm"
            minW="40px"
          />
        ) : (
          <IconButton
            icon={<FiSend />}
            onClick={handleSend}
            aria-label="Send message"
            colorScheme="blue"
            size="sm"
            minW="40px"
            isDisabled={!input.trim() || disabled}
          />
        )}
      </HStack>
    </Box>
  );
};

export default ChatInput;
