import {
  Box,
  Badge,
  Text,
  Spinner,
  Flex,
  useDisclosure,
  Collapse,
} from "@chakra-ui/react";
import { FiCheck, FiAlertCircle, FiChevronDown, FiChevronRight } from "react-icons/fi";
import type { ActiveToolCall } from "@/stores/chatStore";

interface ToolCallDisplayProps {
  toolCall: ActiveToolCall;
}

const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({ toolCall }) => {
  const { isOpen, onToggle } = useDisclosure({ defaultIsOpen: false });

  const statusIcon =
    toolCall.status === "running" ? (
      <Spinner size="xs" color="blue.300" />
    ) : toolCall.status === "done" ? (
      <FiCheck color="var(--chakra-colors-green-300)" />
    ) : (
      <FiAlertCircle color="var(--chakra-colors-red-300)" />
    );

  const formatJson = (str: string): string => {
    try {
      return JSON.stringify(JSON.parse(str), null, 2);
    } catch {
      return str;
    }
  };

  return (
    <Box
      bg="gray.750"
      border="1px solid"
      borderColor="gray.600"
      borderRadius="md"
      fontSize="xs"
      overflow="hidden"
      my={1}
    >
      <Flex
        align="center"
        gap={2}
        px={2}
        py={1.5}
        cursor="pointer"
        onClick={onToggle}
        _hover={{ bg: "gray.700" }}
      >
        {statusIcon}
        <Badge colorScheme="purple" fontSize="xs" variant="subtle">
          {toolCall.tool_name}
        </Badge>
        <Box ml="auto">
          {isOpen ? <FiChevronDown size={12} /> : <FiChevronRight size={12} />}
        </Box>
      </Flex>

      <Collapse in={isOpen}>
        <Box px={2} pb={2}>
          {toolCall.arguments && (
            <Box mb={1}>
              <Text color="gray.400" fontSize="xs" mb={0.5}>
                Arguments:
              </Text>
              <Box
                bg="gray.800"
                p={1.5}
                borderRadius="sm"
                maxH="100px"
                overflowY="auto"
              >
                <Text
                  fontFamily="mono"
                  fontSize="xs"
                  color="gray.300"
                  whiteSpace="pre-wrap"
                  wordBreak="break-all"
                >
                  {formatJson(toolCall.arguments)}
                </Text>
              </Box>
            </Box>
          )}

          {toolCall.result && (
            <Box>
              <Text color="gray.400" fontSize="xs" mb={0.5}>
                Result:
              </Text>
              <Box
                bg="gray.800"
                p={1.5}
                borderRadius="sm"
                maxH="150px"
                overflowY="auto"
              >
                <Text
                  fontFamily="mono"
                  fontSize="xs"
                  color="gray.300"
                  whiteSpace="pre-wrap"
                  wordBreak="break-all"
                >
                  {toolCall.result.length > 1000
                    ? toolCall.result.slice(0, 1000) + "..."
                    : toolCall.result}
                </Text>
              </Box>
            </Box>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

export default ToolCallDisplay;
