import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Text,
  Box,
  Badge,
  Spinner,
  useToast,
  Divider,
  Code,
  Tooltip,
  IconButton,
} from '@chakra-ui/react';
import { CheckIcon, CloseIcon, InfoIcon } from '@chakra-ui/icons';
import { createAuthHeaders } from '../../../api/authHeaders';

interface ParameterSuggestion {
  value: any;
  source: string;
  confidence: number;
  description: string;
  species?: string | null;
  citation?: string | null;
  metadata?: Record<string, any>;
}

interface ParameterSuggestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  parameterName: string;
  parameterDescription: string;
  nodeType?: string;
  species?: string;
  onAccept: (suggestion: ParameterSuggestion) => void;
}

const ParameterSuggestionModal: React.FC<ParameterSuggestionModalProps> = ({
  isOpen,
  onClose,
  parameterName,
  parameterDescription,
  nodeType,
  species,
  onAccept,
}) => {
  const [suggestions, setSuggestions] = useState<ParameterSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  // Define fetchSuggestions before useEffect (to avoid hoisting issues)
  const fetchSuggestions = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query parameters
      const params = new URLSearchParams({
        parameter_name: parameterName,
        parameter_description: parameterDescription,
      });

      if (nodeType) {
        params.append('node_type', nodeType);
      }
      if (species) {
        params.append('species', species);
      }

      // Use relative path - Vite proxy will handle routing to backend
      // In Docker, the proxy is configured to route /api to backend:3000
      // In local dev, it routes to localhost:3000
      const apiUrl = `/api/metadata/parameters/suggest/?${params.toString()}`;
      const headers = await createAuthHeaders();

      const response = await fetch(apiUrl, {
        credentials: 'include',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const suggestionsList = Array.isArray(data.suggestions) ? data.suggestions : [];
      
      // Set suggestions state
      setSuggestions(suggestionsList);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch suggestions';
      setError(errorMessage);
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [parameterName, parameterDescription, nodeType, species, toast]);

  // Fetch suggestions when modal opens
  useEffect(() => {
    if (isOpen && parameterName && parameterDescription) {
      // Reset state before fetching new suggestions
      setSuggestions([]);
      setError(null);
      setLoading(true);
      fetchSuggestions();
    } else if (!isOpen) {
      // Reset state when modal closes
      setSuggestions([]);
      setError(null);
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, parameterName, parameterDescription]); // Only depend on these to avoid duplicate calls

  const handleAccept = (suggestion: ParameterSuggestion) => {
    onAccept(suggestion);
    toast({
      title: 'Suggestion Accepted',
      description: `Parameter "${parameterName}" updated to ${JSON.stringify(suggestion.value)}`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
    onClose();
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'green';
    if (confidence >= 0.6) return 'yellow';
    return 'orange';
  };

  const formatValue = (value: any) => {
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay />
      <ModalContent bg="gray.800" color="white">
        <ModalHeader>
          <VStack align="start" spacing={1}>
            <Text>Parameter Suggestions</Text>
            <Text fontSize="sm" color="gray.400" fontWeight="normal">
              for "{parameterName}"
            </Text>
          </VStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          {loading ? (
            <VStack spacing={4} py={8}>
              <Spinner size="xl" color="blue.400" />
              <Text color="gray.400">Fetching suggestions...</Text>
            </VStack>
          ) : error ? (
            <VStack spacing={4} py={8}>
              <Text color="red.400" fontSize="lg">
                Error: {error}
              </Text>
              <Button colorScheme="blue" onClick={fetchSuggestions}>
                Retry
              </Button>
            </VStack>
          ) : suggestions.length === 0 ? (
            <VStack spacing={4} py={8}>
              <Text color="gray.400" fontSize="lg">
                No suggestions available
              </Text>
              <Text color="gray.500" fontSize="sm" textAlign="center">
                The parameter metadata service could not find any suggestions for this parameter.
                This might be because:
                <br />
                • The parameter description doesn't match known patterns
                <br />
                • No data is available for this parameter type
                <br />
                • The metadata service is using stub data (waiting for API credentials)
              </Text>
            </VStack>
          ) : (
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color="gray.400">
                Found {suggestions.length} suggestion{suggestions.length !== 1 ? 's' : ''}:
              </Text>
              {suggestions.map((suggestion, index) => (
                <Box
                  key={index}
                  p={4}
                  bg="gray.700"
                  borderRadius="md"
                  borderWidth="1px"
                  borderColor="blue.400"
                >
                  <VStack align="stretch" spacing={3}>
                    {/* Header with value and confidence */}
                    <HStack justify="space-between" align="start">
                      <VStack align="start" spacing={1} flex="1">
                        <HStack spacing={2}>
                          <Text fontWeight="bold" fontSize="lg" color="blue.200">
                            Suggested Value:
                          </Text>
                          <Code
                            colorScheme="blue"
                            fontSize="md"
                            bg="gray.600"
                            color="white"
                            px={2}
                            py={1}
                            borderRadius="md"
                          >
                            {formatValue(suggestion.value)}
                          </Code>
                        </HStack>
                        {suggestion.species && (
                          <Badge colorScheme="purple" fontSize="xs">
                            Species: {suggestion.species}
                          </Badge>
                        )}
                      </VStack>
                      <Badge
                        colorScheme={getConfidenceColor(suggestion.confidence)}
                        fontSize="sm"
                        px={2}
                        py={1}
                      >
                        {Math.round(suggestion.confidence * 100)}% confidence
                      </Badge>
                    </HStack>

                    <Divider borderColor="gray.600" />

                    {/* Description */}
                    {suggestion.description && (
                      <Box>
                        <HStack spacing={2} mb={1}>
                          <InfoIcon color="gray.400" boxSize={3} />
                          <Text fontSize="xs" color="gray.400" fontWeight="semibold">
                            Description:
                          </Text>
                        </HStack>
                        <Text fontSize="sm" color="gray.300" pl={5}>
                          {suggestion.description}
                        </Text>
                      </Box>
                    )}

                    {/* Source */}
                    <Box>
                      <HStack spacing={2} mb={1}>
                        <Text fontSize="xs" color="gray.400" fontWeight="semibold">
                          Source:
                        </Text>
                        <Badge colorScheme="cyan" fontSize="xs">
                          {suggestion.source}
                        </Badge>
                      </HStack>
                    </Box>

                    {/* Citation */}
                    {suggestion.citation && (
                      <Box>
                        <Text fontSize="xs" color="gray.400" fontWeight="semibold" mb={1}>
                          Citation:
                        </Text>
                        <Text fontSize="xs" color="gray.400" fontStyle="italic" pl={2}>
                          {suggestion.citation}
                        </Text>
                      </Box>
                    )}

                    {/* Action buttons */}
                    <HStack justify="flex-end" spacing={2} pt={2}>
                      <Button
                        size="sm"
                        colorScheme="green"
                        leftIcon={<CheckIcon />}
                        onClick={() => handleAccept(suggestion)}
                      >
                        Accept
                      </Button>
                      <Button size="sm" variant="ghost" onClick={onClose}>
                        Cancel
                      </Button>
                    </HStack>
                  </VStack>
                </Box>
              ))}
            </VStack>
          )}
        </ModalBody>
        <ModalFooter>
          <Button colorScheme="blue" variant="ghost" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ParameterSuggestionModal;

