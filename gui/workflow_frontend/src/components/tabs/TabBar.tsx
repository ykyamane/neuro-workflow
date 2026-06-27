import React from 'react';
import {
  Box,
  HStack,
  Text,
  IconButton,
  Tooltip,
  useColorModeValue,
} from '@chakra-ui/react';
import { CloseIcon } from '@chakra-ui/icons';
import { useTabContext } from './TabManager';

const TabBar: React.FC = () => {
  const { tabs, activeTabId, switchTab, closeTab } = useTabContext();

  // dark: original grays | light: OpenAI-inspired subtle grays
  const barBg          = useColorModeValue('#f0f0f0', 'gray.800');
  const barBorder      = useColorModeValue('#e5e5e5', 'gray.700');
  const activeTabBg    = useColorModeValue('white', 'gray.700');
  const inactiveHoverBg = useColorModeValue('#e8e8e8', 'gray.750');
  const activeTabText  = useColorModeValue('#1a1a1a', 'white');
  const inactiveTabText = useColorModeValue('gray.500', 'gray.300');

  return (
    <Box
      bg={barBg}
      borderBottom="1px"
      borderColor={barBorder}
      py={0}
      px={2}
      minHeight="42px"
      display="flex"
      alignItems="center"
    >
      <HStack spacing={1} align="center" h="100%">
        {tabs.map((tab) => (
          <Box
            key={tab.id}
            position="relative"
            display="flex"
            alignItems="center"
          >
            <Box
              cursor="pointer"
              onClick={() => switchTab(tab.id)}
              bg={tab.isActive ? activeTabBg : 'transparent'}
              borderTopRadius="6px"
              borderBottom="none"
              px={4}
              py={2}
              height="38px"
              display="flex"
              alignItems="center"
              gap={2}
              transition="all 0.2s ease-in-out"
              _hover={{
                bg: tab.isActive ? activeTabBg : inactiveHoverBg,
              }}
              borderTop="2px solid"
              borderLeft="1px solid"
              borderRight="1px solid"
              borderColor={tab.isActive ? 'blue.400' : barBorder}
              borderTopColor={tab.isActive ? 'blue.400' : 'transparent'}
              maxW="250px"
              position="relative"
              zIndex={tab.isActive ? 2 : 1}
            >
              {/* tab icon */}
              <Text fontSize="sm">
                {tab.type === 'workflow' ? '🔬' : tab.type === 'viewer' ? '🧠' : '📊'}
              </Text>

              {/* tab title */}
              <Text
                fontSize="sm"
                fontWeight={tab.isActive ? '600' : '400'}
                color={tab.isActive ? activeTabText : inactiveTabText}
                isTruncated
                maxW="160px"
              >
                {tab.title}
              </Text>

              {/* Close button (non-workflow tabs only) */}
              {tab.type !== 'workflow' && (
                <Tooltip label="Close tab" fontSize="xs">
                  <IconButton
                    aria-label="Close tab"
                    icon={<CloseIcon />}
                    size="xs"
                    variant="ghost"
                    borderRadius="full"
                    w="20px"
                    h="20px"
                    minW="20px"
                    color={tab.isActive ? inactiveTabText : 'gray.400'}
                    _hover={{
                      bg: 'red.500',
                      color: 'white',
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      closeTab(tab.id);
                    }}
                  />
                </Tooltip>
              )}
            </Box>
          </Box>
        ))}

        {/* empty space */}
        <Box flex="1" height="100%" />
      </HStack>
    </Box>
  );
};

export default TabBar;
