import { useState, useEffect } from 'react';
import { Handle, Node, NodeProps, Position, useUpdateNodeInternals } from "@xyflow/react";
import { CalculationNodeData } from "../type";
import { 
  Badge, 
  Box, 
  Text, 
  HStack, 
  useToast,
  IconButton, 
  Tooltip, Icon } from "@chakra-ui/react";
import { EditIcon, DeleteIcon, ChevronDownIcon, ChevronUpIcon } from "@chakra-ui/icons";
import { FiCode, FiEye } from "react-icons/fi";
import { useTabContext } from '../../../components/tabs/TabManager';
import { JUPYTER_BASE_URL } from '../../../config/urls';
import { generateHandleId } from '@/utils/handleId';
import { createAuthHeaders } from '../../../api/authHeaders';

interface NodeCallbacks {
  onJupyter?: (nodeId: string) => void;
  onInfo?: (nodeId: string) => void;
  onDelete?: (nodeId: string) => void;
  onNodeUpdate?: (nodeId: string, updatedData: Partial<CalculationNodeData>) => void;
}

export const CalculationNode = ({ 
  id, 
  data, 
  isConnectable, 
  selected,
  ...callbacks 
}: NodeProps<Node<CalculationNodeData>> & NodeCallbacks) => {
  const schema = data.schema || { inputs: {}, outputs: {}, parameters: {} };
  const toast = useToast();

  //console.log("This is the schema data", schema);
  //console.log("Node data timestamp:", data.__timestamp || 'no timestamp');

  // Convert inputs and outputs to arrays
  const inputEntries = schema.inputs ? Object.entries(schema.inputs) : [];
  const outputEntries = schema.outputs ? Object.entries(schema.outputs) : [];

  // Use the tab system context
  const { addJupyterTab, addViewerTab } = useTabContext();

  // Combine all fields (inputs first, outputs second)
  const allFields = [
    ...inputEntries.map(([name, data]) => ({
      name,
      type: data.type || 'any',
      description: data.description,
      port_direction: 'input',
      optional: data.optional,
    })),
    ...outputEntries.map(([name, data]) => ({
      name,
      type: data.type || 'any',
      description: data.description,
      port_direction: 'output',
      optional: data.optional,
    }))
  ];

  // Input/output parameter expansion/contraction management
  const [isParamExpand, setIsParamExpand] = useState<boolean>(data.isParamExpand ?? true);
  const updateNodeInternals = useUpdateNodeInternals();
  //const isParamExpand = data.isParamExpand || false;

  useEffect(() => {
    updateNodeInternals(id);
  }, [isParamExpand, id, updateNodeInternals]);

  // Open Jupyter in a new tab
  const OpenJupyter = (filename : string, category : string) => {
    const jupyterUrl = JUPYTER_BASE_URL+"/user/user1/lab/workspaces/auto-E/tree/codes/nodes/"+category.replace('/','').toLowerCase()+"/"+filename;
    
    let projectId = localStorage.getItem('projectId');
    projectId = projectId ? projectId : "";
    // Create new tab
    addJupyterTab(projectId, filename, jupyterUrl);
  };

  const normalizeProjectFolderName = (projectName: string) => {
    const trimmed = projectName.replace(/\s/g, '').toLowerCase();
    return trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
  };

  const normalizeViewerOutputDir = (rawOutputDir?: unknown) => {
    const fallback = 'results/viewer';

    if (typeof rawOutputDir !== 'string' || rawOutputDir.trim() === '') {
      return fallback;
    }

    let normalized = rawOutputDir.trim().replace(/\\/g, '/');

    normalized = normalized.replace(/^\.\/+/, '');
    normalized = normalized.replace(/^\/+/, '');

    const projectsMarker = 'codes/projects/';
    const markerIndex = normalized.indexOf(projectsMarker);
    if (markerIndex >= 0) {
      normalized = normalized.slice(markerIndex + projectsMarker.length);
      const parts = normalized.split('/').filter(Boolean);
      if (parts.length > 1) {
        normalized = parts.slice(1).join('/');
      }
    }

    return normalized || fallback;
  };

  const isBrainViewerNode = () => (
    data.file_name === 'TVBMarmosetBrainViewerNode.py' ||
    data.label === 'TVBMarmosetBrainViewerNode' ||
    data.label === 'MarmosetBrainViewer'
  );

  const handleOpenBrainViewer = async () => {
    const projectId = localStorage.getItem('projectId');
    if (!projectId) {
      toast({
        title: "No Project Selected",
        description: "Please select a project first",
        status: "warning",
        duration: 2500,
        isClosable: true,
      });
      return;
    }

    try {
      const headers = await createAuthHeaders();
      const response = await fetch(`/api/workflow/${projectId}/`, {
        credentials: 'include',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to load project metadata (${response.status})`);
      }

      const project = await response.json();
      const projectFolder = normalizeProjectFolderName(project?.name || projectId);
      const configuredOutputDir = data.schema?.parameters?.output_dir?.default_value;
      const viewerOutputDir = normalizeViewerOutputDir(configuredOutputDir);
      const dataPath = `/api/viewer/${projectFolder}/${viewerOutputDir}/connectivity_data.json`;
      // Cache-buster so re-opening an existing viewer tab forces the iframe to reload fresh data
      const viewerUrl = `/brain-viewer.html?data=${encodeURIComponent(dataPath)}&reload=${Date.now()}`;

      const tabId = `viewer-${projectId}-${viewerOutputDir}`.replace(/[^a-zA-Z0-9_-]/g, '-');
      const tabTitle = `${project?.name || 'Brain'} Viewer`;
      addViewerTab(tabId, tabTitle, viewerUrl);
    } catch (error) {
      console.error('Error opening brain viewer:', error);
      toast({
        title: "Viewer Error",
        description: error instanceof Error ? error.message : "Failed to open brain viewer",
        status: "error",
        duration: 3500,
        isClosable: true,
      });
    }
  };

  return (
    <Box
      bg="white"
      border="2px solid"
      borderColor={selected ? "purple.500" : "#e2e8f0"}
      borderRadius="lg"
      minWidth="200px"
      maxWidth="280px"
      boxShadow={selected ? "lg" : "md"}
      _hover={{ boxShadow: "lg", borderColor: "purple.400" }}
      position="relative"
      transition="all 0.2s"
      role="group"
    >
      {/* header */}
      <Box 
        //bg={selected ? "purple.300" : "purple.300"}
        bg={data.color}
        color="white" 
        p={2} 
        borderTopRadius="lg"
        fontWeight="bold"
        fontSize="sm"
        transition="all 0.2s"
      >
        {/* Node name (center) */}
        <HStack justify="space-between" align="center">
          <Text fontSize="sm" fontWeight="bold" flex="1" textAlign="center">
            {data.instanceName || data.label || data.file_name || data.nodeType || 'Unnamed Node'}
          </Text>
        </HStack>
      </Box>
      
      {/* Button field */}
      <Box 
        bg={selected ? "purple.100" : "gray.50"}
        borderBottom="1px solid #e2e8f0"
        px={2}
        py={1}
        display="flex"
        justifyContent="center"
        opacity={0.8}
        _groupHover={{ opacity: 1 }}
        transition="all 0.2s"
      >
        <HStack spacing={1}>
          <Tooltip label="Open Jupyter" hasArrow>
            <IconButton
              aria-label="Open Jupyter"
              size="xs"
              variant="solid"
              bg="orange.400"
              color="white"
              icon={<Icon as={FiCode} boxSize={2.5} />}
              onClick={(e) => {
                e.stopPropagation();
                //callbacks.onJupyter?.(id);
                OpenJupyter(data.file_name, data.nodeType ?? 'analysis');
              }}
              _hover={{ bg: "orange.500", transform: "scale(1.1)" }}
              minW="18px"
              h="18px"
              borderRadius="sm"
              boxShadow="sm"
            />
          </Tooltip>
          {isBrainViewerNode() && (
            <Tooltip label="Open Brain Viewer" hasArrow>
              <IconButton
                aria-label="Open Brain Viewer"
                size="xs"
                variant="solid"
                bg="teal.400"
                color="white"
                icon={<Icon as={FiEye} boxSize={2.5} />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleOpenBrainViewer();
                }}
                _hover={{ bg: "teal.500", transform: "scale(1.1)" }}
                minW="18px"
                h="18px"
                borderRadius="sm"
                boxShadow="sm"
              />
            </Tooltip>
          )}
          <Tooltip label="Edit Node" hasArrow>
            <IconButton
              aria-label="Edit Node"
              size="xs"
              variant="solid"
              bg="green.400"
              color="white"
              icon={<EditIcon boxSize={2.5} />}
              onClick={(e) => {
                e.stopPropagation();
                callbacks.onInfo?.(id);
              }}
              _hover={{ bg: "green.500", transform: "scale(1.1)" }}
              minW="18px"
              h="18px"
              borderRadius="sm"
              boxShadow="sm"
            />
          </Tooltip>
          <Tooltip label="Delete Node" hasArrow>
            <IconButton
              aria-label="Delete Node"
              size="xs"
              variant="solid"
              bg="red.400"
              color="white"
              icon={<DeleteIcon boxSize={2.5} />}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                callbacks.onDelete?.(id);
              }}
              _hover={{ bg: "red.500", transform: "scale(1.1)" }}
              minW="18px"
              h="18px"
              borderRadius="sm"
              boxShadow="sm"
            />
          </Tooltip>
          <Tooltip label={isParamExpand ? "Collapse Ports" : "Expand Ports"} hasArrow>
            <IconButton
              aria-label="Toggle Ports"
              size="xs"
              variant="solid"
              bg="gray.400"
              color="white"
              icon={isParamExpand ? <ChevronUpIcon boxSize={2.5} /> : <ChevronDownIcon boxSize={2.5} />}
              onClick={(e) => {
                e.stopPropagation();
                const newVal = !isParamExpand;
                setIsParamExpand(newVal);
                callbacks.onNodeUpdate?.(id, { isParamExpand: newVal });
              }}
              _hover={{ bg: "gray.500", transform: "scale(1.1)" }}
              minW="18px"
              h="18px"
              borderRadius="sm"
              boxShadow="sm"
            />
          </Tooltip>
        </HStack>
      </Box>
      

      {/* field display - expanded */}
      {isParamExpand && (
        <Box p={0}>
          {allFields.map((field, index) => {
            const isInput = field.port_direction === 'input';
            const isOutput = field.port_direction === 'output';

            return (
              <Box
                key={`${field.port_direction}-${field.name}`}
                position="relative"
                py={1.5}
                px={3}
                borderBottom={index < allFields.length - 1 ? "1px solid #e2e8f0" : "none"}
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                minHeight="12px"
                bg={isOutput ? 'green.50' : isInput ? 'blue.50' : 'gray.50'}
                _hover={{ bg: isOutput ? 'green.100' : isInput ? 'blue.100' : 'gray.100' }}
                transition="background-color 0.2s"
                height="32px"
              >
                <Text
                  fontSize="xs"
                  fontWeight="medium"
                  color={isOutput ? 'green.700' : isInput ? 'blue.700' : 'gray.700'}
                  maxWidth="150px"
                  isTruncated
                  title={field.description || field.name}
                >
                  {field.name}{ field.optional ? '' : '*' }
                </Text>

                <Badge
                  colorScheme={
                    field.type === 'int' || field.type === 'float' || field.type === 'number' ?
                      (isOutput ? 'green' : isInput ? 'blue' : 'gray') :
                    field.type === 'str' || field.type === 'string' ? 'purple' :
                    field.type === 'bool' || field.type === 'boolean' ? 'orange' :
                    field.type === 'list' || field.type === 'array' || field.type?.includes('[]') ? 'teal' :
                    field.type === 'dict' || field.type === 'object' ? 'yellow' :
                    'gray'
                  }
                  size="sm"
                  fontSize="10px"
                  variant="subtle"
                >
                  {field.type?.includes('[]') ? `${field.type}` : field.type}
                </Badge>

                {/* input handle */}
                {isInput && (
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={generateHandleId(id, field.name, 'input', field.type)}
                    style={{
                      background: '#3182ce',
                      border: '2px solid #fff',
                      width: 12,
                      height: 12,
                      left: -6,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      position: 'absolute',
                      boxShadow: '0 0 0 2px #3182ce40',
                    }}
                    isConnectable={isConnectable}
                  />
                )}

                {/* output handle */}
                {isOutput && (
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={generateHandleId(id, field.name, 'output', field.type)}
                    style={{
                      background: '#38a169',
                      border: '2px solid #fff',
                      width: 12,
                      height: 12,
                      right: -6,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      position: 'absolute',
                      boxShadow: '0 0 0 2px #38a16940',
                    }}
                    isConnectable={isConnectable}
                  />
                )}
              </Box>
            );
          })}
        </Box>
      )}

      {/* field display - collapsed (handles only) */}
      {!isParamExpand && (
        <Box position="relative" minHeight="20px">
          {/* Input Handles - left side, evenly distributed */}
          {inputEntries.map(([name, data], index) => (
            <Handle
              key={`collapsed-input-${name}`}
              type="target"
              position={Position.Left}
              id={generateHandleId(id, name, 'input', data.type || 'any')}
              style={{
                background: '#3182ce',
                border: '2px solid #fff',
                width: 10,
                height: 10,
                left: -5,
                top: `${((index + 1) / (inputEntries.length + 1)) * 100}%`,
                position: 'absolute',
                boxShadow: '0 0 0 2px #3182ce40',
              }}
              isConnectable={isConnectable}
            />
          ))}
          {/* Output Handles - right side, evenly distributed */}
          {outputEntries.map(([name, data], index) => (
            <Handle
              key={`collapsed-output-${name}`}
              type="source"
              position={Position.Right}
              id={generateHandleId(id, name, 'output', data.type || 'any')}
              style={{
                background: '#38a169',
                border: '2px solid #fff',
                width: 10,
                height: 10,
                right: -5,
                top: `${((index + 1) / (outputEntries.length + 1)) * 100}%`,
                position: 'absolute',
                boxShadow: '0 0 0 2px #38a16940',
              }}
              isConnectable={isConnectable}
            />
          ))}
        </Box>
      )}
      
      {/* Debug information (displayed only during development) */}
      {process.env.NODE_ENV === 'development' && (
        <Box
          position="absolute"
          bottom="-20px"
          left="0"
          fontSize="8px"
          color="gray.500"
          bg="white"
          px={1}
          borderRadius="sm"
          border="1px solid #e2e8f0"
        >
          ID: {id}
        </Box>
      )}
    </Box>
  );
};
