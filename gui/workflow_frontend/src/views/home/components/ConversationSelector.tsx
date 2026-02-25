import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  Button,
  Text,
  Flex,
  IconButton,
  useColorModeValue,
} from "@chakra-ui/react";
import { FiChevronDown, FiTrash2 } from "react-icons/fi";
import type { ConversationSummary } from "@/stores/chatStore";

interface ConversationSelectorProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNew: () => void;
}

const ConversationSelector: React.FC<ConversationSelectorProps> = ({
  conversations,
  activeConversationId,
  onSelect,
  onDelete,
  onNew,
}) => {
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('#e5e5e5', 'gray.600');
  const subtextColor = useColorModeValue('gray.500', 'gray.300');
  const hoverBg = useColorModeValue('#f5f5f5', 'gray.700');
  const activeBg = useColorModeValue('#ebebeb', 'gray.700');

  const active = conversations.find((c) => c.id === activeConversationId);

  return (
    <Menu>
      <MenuButton
        as={Button}
        rightIcon={<FiChevronDown />}
        size="xs"
        variant="ghost"
        color={subtextColor}
        maxW="180px"
        fontWeight="normal"
        _hover={{ bg: hoverBg }}
      >
        <Text isTruncated fontSize="xs">
          {active ? active.title : "New Chat"}
        </Text>
      </MenuButton>
      <MenuList bg={bg} borderColor={borderColor} minW="220px" zIndex={2000}>
        <MenuItem
          fontSize="xs"
          bg={bg}
          _hover={{ bg: hoverBg }}
          onClick={onNew}
        >
          + New Conversation
        </MenuItem>
        {conversations.length > 0 && <MenuDivider borderColor={borderColor} />}
        {conversations.map((conv) => (
          <MenuItem
            key={conv.id}
            fontSize="xs"
            bg={conv.id === activeConversationId ? activeBg : bg}
            _hover={{ bg: hoverBg }}
            onClick={() => onSelect(conv.id)}
          >
            <Flex justify="space-between" align="center" w="100%">
              <Text isTruncated maxW="160px">
                {conv.title}
              </Text>
              <IconButton
                icon={<FiTrash2 />}
                aria-label="Delete conversation"
                size="xs"
                variant="ghost"
                color="gray.500"
                _hover={{ color: "red.300" }}
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
              />
            </Flex>
          </MenuItem>
        ))}
      </MenuList>
    </Menu>
  );
};

export default ConversationSelector;
