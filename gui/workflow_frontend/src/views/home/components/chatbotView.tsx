import KeywordSearch from '@/shared/keyWordSearch/keyWordSearch';
import {
  VStack,
  Box,
  Text,
  Flex,
  SimpleGrid,
  Icon,
  Heading,
  Divider,
  Spinner,
  IconButton,
  HStack,
  useToast,
  Input,
  Button,
  useDisclosure,
  Tooltip,
  Collapse,
  Badge,
} from '@chakra-ui/react';
import { useEffect, useState, useRef } from 'react';
import { IconType } from 'react-icons';
import { FiBox, FiCopy, FiTrash2, FiInfo, FiCode, FiRefreshCw, FiChevronDown, FiChevronRight, FiMenu, FiX } from 'react-icons/fi'; // Use as default icon
import { IoChatboxEllipses } from "react-icons/io5";
import { SchemaFields } from '../home/type';
import { createAuthHeaders } from '../../api/authHeaders';

interface ChatbotProps {
  isLoading?: boolean;
  error?: string;
}

const SIDEBAR_WIDTH = '600px'; // Width when opened
const TOGGLE_WIDTH = '16px'; // Knob width when closed

const ChatbotArea: React.FC<ChatbotProps> = ({isLoading = false, error}) => {
  const toast = useToast();

  const { isOpen, onToggle } = useDisclosure({ defaultIsOpen: false });

  return (
    <Flex 
        height="calc(100vh - 340px)" 
        overflow="hidden" 
        position="absolute"
        top="330px"
        left="8px"
        zIndex="1010">
      <Box
        bg="gray.800"
        color="white"
        height="100%"
        width={isOpen ? SIDEBAR_WIDTH : TOGGLE_WIDTH}
        transition="width 0.3s ease-in-out"
        overflow="hidden"
        position="relative"
        flexShrink={0}
      >
        <Flex
          direction="column"
          align="stretch"
          height="100%"
          width={SIDEBAR_WIDTH}
          transition="transform 0.3s ease-in-out"
          transform={isOpen ? 'translateX(0)' : `translateX(-${SIDEBAR_WIDTH} + ${TOGGLE_WIDTH})`}
        >
          <IconButton
            icon={isOpen ? <FiX /> : <FiMenu />}
            onClick={onToggle}
            aria-label={isOpen ? "Close Sidebar" : "Open Sidebar"}
            position="absolute"
            top="50%"
            transform="translateY(-50%)"
            right="0"
            zIndex="1020"
            bg="gray.700"
            color="white"
            width="12px"
            height="64px"
            _hover={{ bg: "blue.600" }}
          />
          <VStack spacing={4} align="stretch" p="1" pt="1">
            <Box height="calc(100vh - 260px)">
              <iframe
                  src="https://chakra-ui.com"
                  width="100%"
                  height="100%"
                  style={{ border: "none" }}
                  title="Chakra UI Site"
                />
            </Box>
          </VStack>
        </Flex>
      </Box>
    </Flex>
  );
};

export default ChatbotArea;
