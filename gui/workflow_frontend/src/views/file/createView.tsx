import React, { useState } from 'react';
import {
  Box,
  Button,
  Text,
  Input,
  VStack,
  useToast,
  FormControl,
  FormLabel,
  Textarea,
  Grid,
  GridItem,
  Divider,
  Spinner,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { createAuthHeaders } from '../../api/authHeaders'; // for authentication header

interface CreateFlowProjectRequest {
  name: string;
  description: string;
}

interface CreateFlowProjectResponse {
  id: string;  // UUID is a string
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  owner?: number;
}

interface ErrorResponse {
  error: string;
  details?: string;
}

const CreateFlowPj: React.FC = () => {
  const [projectName, setProjectName] = useState<string>('');
  const [note, setNote] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const toast = useToast();
  const navigate = useNavigate();

  // Backend Workflow API endpoints
  const API_ENDPOINT = `/api/workflow/`;

  // Workflow project creation API call
  const createFlowProject = async (data: CreateFlowProjectRequest): Promise<CreateFlowProjectResponse> => {
    try {
      console.log('Creating flow project with data:', data);
      
      // Get authentication header
      const authHeaders = await createAuthHeaders();
      
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        credentials: 'include',  // Include Cookies (Sessions)
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorData: ErrorResponse = await response.json();
        console.error('API error response:', errorData);
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result: CreateFlowProjectResponse = await response.json();
      console.log('Project created successfully:', result);
      return result;
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  };

  const handleRegistration = async () => {
    if (!projectName.trim()) {
      toast({
        title: 'Input Error',
        description: 'Please enter a project name',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);

    try {
      // Prepare data for API calls
      const requestData: CreateFlowProjectRequest = {
        name: projectName.trim(),
        description: note.trim() || '', // Default to empty string
      };

      const response = await createFlowProject(requestData);

      // Processing on success
      toast({
        title: 'Creation Success',
        description: `"${response.name}" has been created successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      // reset form
      setProjectName('');
      setNote('');

      // Go to the details screen of the created workflow (using UUID)
      // navigate(`/workflow/${response.id}`);
      navigate(`/`);

    } catch (error) {
      console.error('Error creating flow project:', error);
      
      let errorMessage = 'An unexpected error occurred';
      
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      // Detailed message for the specific error
      if (errorMessage.includes('401')) {
        errorMessage = 'Authentication required. Please login first.';
      } else if (errorMessage.includes('403')) {
        errorMessage = 'Permission denied. You do not have access to create projects.';
      } else if (errorMessage.includes('400')) {
        errorMessage = 'Invalid project data. Please check your input.';
      } else if (errorMessage.includes('500')) {
        errorMessage = 'Server error. Please try again later.';
      }
      
      toast({
        title: 'Creation Failed',
        description: errorMessage,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setProjectName('');
    setNote('');
    navigate(-1);
  };

  return (
    <Box height="100%" width="100%" overflow="auto" bg="gray.900">
      <VStack spacing={6} width="100%" p={6} maxWidth="600px" mx="auto" minHeight="100vh">
      <Text fontSize="2xl" fontWeight="bold" mb={2} color="white">
        🚀 Create Flow Project
      </Text>

      <Text fontSize="md" color="white" textAlign="center" mb={2}>
        Create a new workflow project to design mathematical calculations
      </Text>

      <Divider my={4} />

      <VStack width="100%" spacing={5} align="start">
        <FormControl isRequired>
          <FormLabel htmlFor="projectName" fontSize="sm" fontWeight="semibold" color="white">
            Project Name
          </FormLabel>
          <Input 
            id="projectName" 
            placeholder="Enter your project name..."
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            isDisabled={isLoading}
            size="md"
            borderColor="gray.300"
            _hover={{ borderColor: "blue.300" }}
            _focus={{ borderColor: "blue.500", boxShadow: "0 0 0 1px #3182ce" }}
          />
        </FormControl>

        <FormControl>
          <FormLabel htmlFor="note" fontSize="sm" fontWeight="semibold" color="white">
            Description (Optional)
          </FormLabel>
          <Textarea
            id="note"
            placeholder="Describe your workflow project..."
            rows={4}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            isDisabled={isLoading}
            borderColor="gray.300"
            _hover={{ borderColor: "blue.300" }}
            _focus={{ borderColor: "blue.500", boxShadow: "0 0 0 1px #3182ce" }}
            resize="vertical"
          />
        </FormControl>
      </VStack>

      <Grid templateColumns="repeat(2, 1fr)" gap={4} width="100%" mt={6}>
        <GridItem>
          <Button
            colorScheme="green"
            size="lg"
            width="100%"
            fontWeight="bold"
            isDisabled={!projectName.trim() || isLoading}
            onClick={handleRegistration}
            boxShadow="sm"
            color="white"
            _hover={{ 
              boxShadow: "md", 
              transform: "translateY(-2px)",
              bg: "green.600",
              color: "white"
            }}
            _active={{ transform: "translateY(0)" }}
            transition="all 0.2s"
            leftIcon={isLoading ? <Spinner size="sm" /> : undefined}
          >
            {isLoading ? 'Creating Project...' : 'Create Project'}
          </Button>
        </GridItem>
        <GridItem>
          <Button
            colorScheme="red"
            variant="outline"
            size="lg"
            width="100%"
            onClick={handleCancel}
            _hover={{ 
              bg: "red.50",
              borderColor: "red.300",
              color: "red.600"
            }}
            isDisabled={isLoading}
          >
            Cancel
          </Button>
        </GridItem>
      </Grid>
      </VStack>
    </Box>
  );
};

export default CreateFlowPj;
