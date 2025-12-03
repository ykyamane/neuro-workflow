import { useState, useCallback } from 'react';
import { Project } from '../type'
import {
  HStack,
  Box,
  VStack,
  Select,
  FormLabel,
  Badge,
  Text,
  Flex,
  IconButton,
  Tooltip,
  useToast,
} from '@chakra-ui/react';
import { CheckIcon, WarningIcon, DeleteIcon } from '@chakra-ui/icons';
import { FiMenu, FiPlay } from 'react-icons/fi';
import { useTabContext } from '../../../components/tabs/TabManager';
import { createAuthHeaders } from '../../../api/authHeaders';
import LogViewModal from "./logViewModal"; 

export const ProjectSelector = ({ 
  projects, 
  selectedProject, 
  onProjectChange, 
  onProjectDelete,
  autoSaveEnabled = true,
  isConnected = true 
}: {
  projects: Project[];
  selectedProject: string | null;
  onProjectChange: (projectId: string) => void;
  onProjectDelete?: (project: Project) => void;
  autoSaveEnabled?: boolean;
  isConnected?: boolean;
}) => {
  const toast = useToast();
  // Island menu opening/closing management
  const [isIslandProjectOpen, setIslandProjectOpen] = useState(true);
  // Use the tab system context
  const { addJupyterTab } = useTabContext();
  // Log View Modal
  const [isLogOpen, setIsLogOpen] = useState<boolean>(false);
  const [logText, setLogText] = useState<string | null>(null);

  // Helper functions for API communication
  const createAuthHeadersLocal = async () => {
    return await createAuthHeaders();
  };

  // Get status badge
  const getStatusBadge = () => {
    if (!isConnected) {
      return (
        <Badge colorScheme="red" size="sm" variant="subtle">
          <HStack spacing={1}>
            <WarningIcon w={2} h={2} />
            <Text fontSize="xs">Offline</Text>
          </HStack>
        </Badge>
      );
    }
    
    if (autoSaveEnabled) {
      return (
        <Badge colorScheme="green" size="sm" variant="subtle">
          <HStack spacing={1}>
            <CheckIcon w={2} h={2} />
            <Text fontSize="xs">Auto-save</Text>
          </HStack>
        </Badge>
      );
    }
    
    return (
      <Badge colorScheme="orange" size="sm" variant="subtle">
        <HStack spacing={1}>
          <WarningIcon w={2} h={2} />
          <Text fontSize="xs">Manual save</Text>
        </HStack>
      </Badge>
    );
  };

  // Get status message
  const getStatusMessage = () => {
    if (!isConnected) {
      return "⚠️ Connection lost - changes not saved";
    }
    if (autoSaveEnabled) {
      return "💾 Changes are automatically saved";
    }
    return "⚠️ Remember to save manually";
  };

  // Viewing the source code of a workflow project
  const handleOpenJupyter = useCallback(async () => {
    if (!selectedProject) {
      toast({
        title: "No Project Selected",
        description: "Please select a project first",
        status: "warning",
        duration: 2000,
        isClosable: true,
      });
      return;
    }

    try {
      let projectId = localStorage.getItem('projectId');
      projectId = projectId ? projectId : "";
      // Get project name
      const projectName = projects.find(p => p.id === selectedProject)?.name || selectedProject;
      // Initial capitalization
      const trimedProjectName = projectName.replace(/\s/g, '').toLowerCase();
      const capitalizedProjectName = trimedProjectName.charAt(0).toUpperCase() + trimedProjectName.slice(1);

      // Build JupyterLab URL (development mode)
      const jupyterBase = ((): string => {
        try {
          if (typeof window === 'undefined') return 'http://localhost:8000';
          const { protocol, hostname, host } = window.location;
          // host includes port if present (hostname:port)
          if (host.includes(':')) {
            return `${protocol}//${hostname}:8000`;
          }
          return `${protocol}//${host}`;
        } catch (e) {
          return 'http://localhost:8000';
        }
      })();
      const jupyterUrl = `${jupyterBase}/user/user1/lab/workspaces/auto-E/tree/codes/projects/${capitalizedProjectName}/${capitalizedProjectName}.py`;
      
      // Create new tab
      addJupyterTab(selectedProject, projectName, jupyterUrl);
      
      toast({
        title: "JupyterLab Tab Created",
        description: `Created tab for project "${projectName}"`,
        status: "success",
        duration: 2000,
        isClosable: true,
      });
      
    } catch (error) {
      console.error('Error creating JupyterLab tab:', error);
      toast({
        title: "Error",
        description: "Failed to create JupyterLab tab",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  }, [selectedProject, projects, addJupyterTab, toast]);

  // Run workflow project
  const handleRunWorkflow = useCallback(async () => {
    if (!selectedProject) {
      toast({
        title: "No Project Selected",
        description: "Please select a project first",
        status: "warning",
        duration: 2000,
        isClosable: true,
      });
      return;
    }

    try {
      const headers = await createAuthHeadersLocal();

      // Get project name
      const projectName = projects.find(p => p.id === selectedProject)?.name || selectedProject;
      // Initial capitalization
      const trimedProjectName = projectName.replace(/\s/g, '');
      const capitalizedProjectName = trimedProjectName.charAt(0).toUpperCase() + trimedProjectName.slice(1);

      const response = await fetch(`/api/workflow/${selectedProject}/run/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: "",
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`HTTP ${response.status}: ${errorData.error || 'Failed to run workflow'}`);
      }
      
      const result = await response.json();
      console.log('Run workflow result:', result);

      let resultResult = JSON.stringify(result.result);
      let resultText = `status: "${result.status}"\n`;
      resultText += `message: "${result.message}"\n`;
      resultText += `project name: "${capitalizedProjectName}"\n`;
      resultText += `result: "${resultResult}"`;

      setLogText(resultText);
      setIsLogOpen(true);

      toast({
        title: "Run Workflow Successfully! ✅",
        description: result.message || "Code has been generated and is ready to use",
        status: "success",
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error run Workflow:', error);
      toast({
        title: "Error",
        description: "Failed to run workflow",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  }, [selectedProject, projects, toast]);

  return (
    <Box
      position="absolute"
      top="8px"
      left="16px"
    >
      <HStack spacing={2}>
        <IconButton
          position="absolute"
          top="16px"
          left="16px"
          zIndex={1000}
          aria-label="Open/close menu"
          icon={<FiMenu />}
          onClick={() => setIslandProjectOpen(!isIslandProjectOpen)}
          colorScheme="gray"
          bg="gray.300"
          _hover={{ bg: 'gray.600' }}
        />
        <IconButton
          position="absolute"
          top="16px"
          left="64px"
          zIndex={1000}
          aria-label="Execute"
          icon={<FiPlay />}
          onClick={() => handleRunWorkflow()}
          colorScheme="gray"
          bg="pink.300"
          _hover={{ bg: 'gray.600' }}
        />
      </HStack>
      <Box
        position="absolute"
        top="0px"
        left="0px"
        p={4}
        bg="white"
        borderRadius="md"
        boxShadow="md"
        zIndex={5}
        minWidth="320px"
        borderWidth={1}
        borderColor="gray.200"
        display={isIslandProjectOpen ? 'block' : 'none'}
      >
        <VStack spacing={3} align="stretch" width="100%">
          {/* header part */}
          <Flex justify="space-between" align="center">
            <Box marginLeft={24}>
              <FormLabel fontSize="sm" mb={0} color="gray.700" fontWeight="semibold">
                Project Workspace
              </FormLabel>
              {getStatusBadge()}
            </Box>
          </Flex>
          
          {/* Project selection */}
          <HStack spacing={2}>
            <Select 
              value={selectedProject || ''} 
              onChange={(e) => onProjectChange(e.target.value)}
              onLoad={(e) => onProjectChange(e.target.value)}
              size="sm"
              bg="white"
              color="gray.800"
              borderColor="gray.300"
              placeholder="Choose a project..."
              _hover={{
                borderColor: "blue.300"
              }}
              _focus={{
                borderColor: "blue.500",
                boxShadow: "0 0 0 1px #3182ce"
              }}
              flex="1"
              marginTop={2}
            >
              {projects.map(project => (
                <option key={project.id} value={project.id} style={{color: '#2D3748'}}>
                  {project.name}
                </option>
              ))}
            </Select>
            
            {selectedProject && onProjectDelete && (
              <Tooltip label="Delete project" placement="top">
                <IconButton
                  aria-label="Delete project"
                  icon={<DeleteIcon />}
                  size="sm"
                  colorScheme="red"
                  variant="outline"
                  onClick={() => {
                    const project = projects.find(p => p.id === selectedProject);
                    if (project) {
                      onProjectDelete(project);
                    }
                  }}
                  _hover={{
                    bg: "red.50",
                    borderColor: "red.400"
                  }}
                  marginTop={2}
                />
              </Tooltip>
            )}
          </HStack>
          
          {/* status message */}
          {selectedProject && (
            <Text 
              fontSize="xs" 
              color={!isConnected ? "red.600" : autoSaveEnabled ? "green.600" : "orange.600"}
              textAlign="center"
              py={1}
              px={2}
              bg={!isConnected ? "red.50" : autoSaveEnabled ? "green.50" : "orange.50"}
              borderRadius="sm"
              borderWidth={1}
              borderColor={!isConnected ? "red.200" : autoSaveEnabled ? "green.200" : "orange.200"}
            >
              {getStatusMessage()}
            </Text>
          )}LogViewDialog
          
          {/* Project information (displayed only when selected) */}
          {selectedProject && (
            <Box pt={2} borderTop="1px" borderColor="gray.100">
              <Text fontSize="xs" color="gray.500">
                Project ID: {selectedProject}
              </Text>
            </Box>
          )}
        </VStack>
      </Box>

      <LogViewModal 
        isOpen={isLogOpen}
        onClose={() => {
          setIsLogOpen(false);
        }}
        logText={logText}
      />
    </Box>
  );
};
