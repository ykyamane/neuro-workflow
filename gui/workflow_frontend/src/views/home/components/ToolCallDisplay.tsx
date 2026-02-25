import {
  Box,
  Badge,
  Text,
  Spinner,
  Flex,
  useDisclosure,
  Collapse,
  useColorModeValue,
} from "@chakra-ui/react";
import { FiCheck, FiAlertCircle, FiChevronDown, FiChevronRight } from "react-icons/fi";
import type { ActiveToolCall } from "@/stores/chatStore";

interface ToolCallDisplayProps {
  toolCall: ActiveToolCall;
}

const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({ toolCall }) => {
  const { isOpen, onToggle } = useDisclosure({ defaultIsOpen: false });

  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('#e5e5e5', 'gray.600');
  const hoverBg = useColorModeValue('#f5f5f5', 'gray.700');
  const subtextColor = useColorModeValue('gray.500', 'gray.400');
  const monoTextColor = useColorModeValue('gray.700', 'gray.300');
  // gray.750 does not exist — map to gray.700 (dark) / #ebebeb (light)
  const outerBg = useColorModeValue('#ebebeb', 'gray.700');

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
      bg={outerBg}
      border="1px solid"
      borderColor={borderColor}
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
        _hover={{ bg: hoverBg }}
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
              <Text color={subtextColor} fontSize="xs" mb={0.5}>
                Arguments:
              </Text>
              <Box
                bg={bg}
                p={1.5}
                borderRadius="sm"
                maxH="100px"
                overflowY="auto"
              >
                <Text
                  fontFamily="mono"
                  fontSize="xs"
                  color={monoTextColor}
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
              <Text color={subtextColor} fontSize="xs" mb={0.5}>
                Result:
              </Text>
              <Box
                bg={bg}
                p={1.5}
                borderRadius="sm"
                maxH="150px"
                overflowY="auto"
              >
                <Text
                  fontFamily="mono"
                  fontSize="xs"
                  color={monoTextColor}
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
