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
  const active = conversations.find((c) => c.id === activeConversationId);

  return (
    <Menu>
      <MenuButton
        as={Button}
        rightIcon={<FiChevronDown />}
        size="xs"
        variant="ghost"
        color="gray.300"
        maxW="180px"
        fontWeight="normal"
        _hover={{ bg: "gray.700" }}
      >
        <Text isTruncated fontSize="xs">
          {active ? active.title : "New Chat"}
        </Text>
      </MenuButton>
      <MenuList bg="gray.800" borderColor="gray.600" minW="220px" zIndex={2000}>
        <MenuItem
          fontSize="xs"
          bg="gray.800"
          _hover={{ bg: "gray.700" }}
          onClick={onNew}
        >
          + New Conversation
        </MenuItem>
        {conversations.length > 0 && <MenuDivider borderColor="gray.600" />}
        {conversations.map((conv) => (
          <MenuItem
            key={conv.id}
            fontSize="xs"
            bg={conv.id === activeConversationId ? "gray.700" : "gray.800"}
            _hover={{ bg: "gray.700" }}
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
