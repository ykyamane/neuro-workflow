import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  useDisclosure,
  TableContainer,
} from '@chakra-ui/react';
import { AddIcon, EditIcon, DeleteIcon, CheckIcon, CloseIcon } from '@chakra-ui/icons';
import CustomDatabaseModal from './CustomDatabaseModal';

interface CustomDatabase {
  id: string;
  name: string;
  description?: string;
  base_url: string;
  api_key?: string;
  adapter_type: string;
  is_active: boolean;
  is_verified: boolean;
  last_tested?: string;
  test_result?: string;
  test_error?: string;
  config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

const CustomDatabaseManager: React.FC = () => {
  const [databases, setDatabases] = useState<CustomDatabase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDatabase, setSelectedDatabase] = useState<CustomDatabase | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const fetchDatabases = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/metadata/custom-databases/');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setDatabases(Array.isArray(data) ? data : []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch databases';
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
  };

  useEffect(() => {
    fetchDatabases();
  }, []);

  const handleAdd = () => {
    setSelectedDatabase(null);
    onOpen();
  };

  const handleEdit = (database: CustomDatabase) => {
    setSelectedDatabase(database);
    onOpen();
  };

  const handleDelete = async (database: CustomDatabase) => {
    if (!window.confirm(`Are you sure you want to delete "${database.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/metadata/custom-databases/${database.id}/`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(errorData.message || errorData.error || `HTTP error! status: ${response.status}`);
      }

      toast({
        title: 'Database Deleted',
        description: `Custom database "${database.name}" deleted successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      fetchDatabases();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete database';
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleModalSuccess = () => {
    fetchDatabases();
  };

  if (loading) {
    return (
      <Box p={4} textAlign="center">
        <Spinner size="xl" />
        <Text mt={4}>Loading custom databases...</Text>
      </Box>
    );
  }

  return (
    <Box p={4}>
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Text fontSize="xl" fontWeight="bold">
            Custom Databases
          </Text>
          <Button
            leftIcon={<AddIcon />}
            onClick={handleAdd}
            colorScheme="blue"
          >
            Add Database
          </Button>
        </HStack>

        {error && (
          <Alert status="error">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {databases.length === 0 ? (
          <Box p={8} textAlign="center" borderWidth={1} borderRadius="md" borderStyle="dashed">
            <Text color="gray.500" mb={4}>
              No custom databases configured yet.
            </Text>
            <Text fontSize="sm" color="gray.400" mb={4}>
              Add a custom database to include it in parameter suggestions alongside
              Allen Brain Atlas, NeuroMorpho, PubMed, and NeuroML-DB.
            </Text>
            <Button leftIcon={<AddIcon />} onClick={handleAdd} colorScheme="blue">
              Add Your First Database
            </Button>
          </Box>
        ) : (
          <TableContainer>
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Name</Th>
                  <Th>Base URL</Th>
                  <Th>Status</Th>
                  <Th>Type</Th>
                  <Th>Last Tested</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {databases.map((db) => (
                  <Tr key={db.id}>
                    <Td>
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="medium">{db.name}</Text>
                        {db.description && (
                          <Text fontSize="sm" color="gray.500">
                            {db.description}
                          </Text>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm" fontFamily="mono">
                        {db.base_url}
                      </Text>
                    </Td>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Badge colorScheme={db.is_verified ? 'green' : 'red'}>
                          {db.is_verified ? (
                            <>
                              <CheckIcon mr={1} /> Verified
                            </>
                          ) : (
                            <>
                              <CloseIcon mr={1} /> Not Verified
                            </>
                          )}
                        </Badge>
                        <Badge colorScheme={db.is_active ? 'green' : 'gray'}>
                          {db.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </VStack>
                    </Td>
                    <Td>
                      <Badge>{db.adapter_type}</Badge>
                    </Td>
                    <Td>
                      {db.last_tested ? (
                        <Text fontSize="sm">
                          {new Date(db.last_tested).toLocaleString()}
                        </Text>
                      ) : (
                        <Text fontSize="sm" color="gray.400">
                          Never
                        </Text>
                      )}
                    </Td>
                    <Td>
                      <HStack spacing={2}>
                        <IconButton
                          aria-label="Edit database"
                          icon={<EditIcon />}
                          size="sm"
                          onClick={() => handleEdit(db)}
                        />
                        <IconButton
                          aria-label="Delete database"
                          icon={<DeleteIcon />}
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => handleDelete(db)}
                        />
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        )}
      </VStack>

      <CustomDatabaseModal
        isOpen={isOpen}
        onClose={onClose}
        database={selectedDatabase}
        onSuccess={handleModalSuccess}
      />
    </Box>
  );
};

export default CustomDatabaseManager;
