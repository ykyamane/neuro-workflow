import { useState, useCallback, useEffect } from 'react';
import { Handle, NodeProps, Position, useUpdateNodeInternals } from "@xyflow/react";
import { CalculationNodeData } from "../type";
import { 
  Badge, 
  Box, 
  Text, 
  HStack, 
  useToast,
  IconButton, 
  Button,
  useDisclosure,
  AlertDialog,
  AlertDialogOverlay,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
  Tooltip, Icon } from "@chakra-ui/react";
import { useRef } from 'react';
import { ViewIcon, InfoIcon, DeleteIcon } from "@chakra-ui/icons";
import { FiCode } from "react-icons/fi";
import { useTabContext } from '../../../components/tabs/TabManager';
import { createAuthHeaders } from '../../../api/authHeaders';

interface NodeCallbacks {
  onJupyter?: (nodeId: string) => void;
  onInfo?: (nodeId: string) => void;
  onDelete?: (nodeId: string) => void;
}

export const CalculationNode = ({ 
  id, 
  data, 
  isConnectable, 
  selected,
  ...callbacks 
}: NodeProps<CalculationNodeData> & NodeCallbacks) => {
  const schema = data.schema || { inputs: {}, outputs: {}, parameters: {} };

  const [nodeToAction, setNodeToAction] = useState<NodeTypeWithIcon | null>(null);
  const { isOpen: isDeleteAlertOpen, onOpen: onDeleteAlertOpen, onClose: onDeleteAlertClose } = useDisclosure();
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const toast = useToast();

  //console.log("This is the schema data", schema);
  //console.log("Node data timestamp:", data.__timestamp || 'no timestamp');

  // A function that generates a unique handle ID
  const generateHandleId = (nodeId: string, fieldName: string, handleType: 'input' | 'output', portType: string) => {
    return `${nodeId}-${fieldName}-${handleType}-${portType}`;
  };
  
  // Convert inputs and outputs to arrays
  const inputEntries = schema.inputs ? Object.entries(schema.inputs) : [];
  const outputEntries = schema.outputs ? Object.entries(schema.outputs) : [];

  // Use the tab system context
  const { addJupyterTab } = useTabContext();

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
  const [isParamExpand, setIsParamExpand] = useState<boolean>(true);
  const updateNodeInternals = useUpdateNodeInternals();
  //const isParamExpand = data.isParamExpand || false;

  useEffect(() => {
    updateNodeInternals(id);
  }, [isParamExpand, id, updateNodeInternals]);

  // Open Jupyter in a new tab
  const OpenJupyter = (filename : string, category : string) => {
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
    // JupyterLab URLを構築（開発モード）
    const jupyterUrl = jupyterBase+"/user/user1/lab/workspaces/auto-E/tree/codes/nodes/"+category.replace('/','').toLowerCase()+"/"+filename;
    
    let projectId = localStorage.getItem('projectId');
    projectId = projectId ? projectId : "";
    // Create new tab
    addJupyterTab(projectId, filename, jupyterUrl);
  };

  // Opens a delete confirmation dialog
  const openDeleteDialog = (node: NodeTypeWithIcon) => {
    if (!node.label) {
      toast({
        title: "Error",
        description: "No label available for deletion",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setNodeToAction(node);
    onDeleteAlertOpen();
  };

// Delete execution on workflow
  const handleDeleteNode = async () => {
    if (!id) return;

    try {
      setIsDeleting(id);
      callbacks.onDelete?.(id);
    } catch (error) {
      console.error('Error deleting node:', error);
      toast({
        title: "Error",
        description: `Failed to delete node: ${error instanceof Error ? error.message : 'Unknown error'}`,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsDeleting(null);
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
            {data.instanceName || data.label }
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
                OpenJupyter(data.file_name, data.nodeType);
              }}
              _hover={{ bg: "orange.500", transform: "scale(1.1)" }}
              minW="18px"
              h="18px"
              borderRadius="sm"
              boxShadow="sm"
            />
          </Tooltip>
          <Tooltip label="Node Info" hasArrow>
            <IconButton
              aria-label="Node Info"
              size="xs"
              variant="solid"
              bg="green.400"
              color="white"
              icon={<InfoIcon boxSize={2.5} />}
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
                //callbacks.onDelete?.(id);
                e.preventDefault();
                openDeleteDialog(data);
              }}
              _hover={{ bg: "red.500", transform: "scale(1.1)" }}
              minW="18px"
              h="18px"
              borderRadius="sm"
              boxShadow="sm"
            />
          </Tooltip>
        </HStack>
      </Box>
      

      {/* field display */}
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
              height={isParamExpand ? '32px' : '12px'}
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

      {/* Delete confirmation alert dialog */}
      <AlertDialog
          isOpen={isDeleteAlertOpen}
          leastDestructiveRef={cancelRef}
          onClose={onDeleteAlertClose}
        >
          <AlertDialogOverlay>
            <AlertDialogContent bg="gray.800" color="white">
              <AlertDialogHeader fontSize="lg" fontWeight="bold">
                Delete Node
              </AlertDialogHeader>

              <AlertDialogBody>
                Are you sure you want to delete "{nodeToAction?.label}"?
                <br />
                <Text fontSize="sm" color="gray.400" mt={2}>
                  This action cannot be undone.
                </Text>
              </AlertDialogBody>

              <AlertDialogFooter>
                <Button 
                  ref={cancelRef} 
                  onClick={onDeleteAlertClose}
                  variant="ghost"
                  color="gray.300"
                >
                  Cancel
                </Button>
                <Button 
                  colorScheme="red" 
                  onClick={handleDeleteNode} 
                  ml={3}
                  isLoading={isDeleting === nodeToAction?.file_id}
                >
                  Delete
                </Button>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialogOverlay>
        </AlertDialog>
    </Box>
  );
};
