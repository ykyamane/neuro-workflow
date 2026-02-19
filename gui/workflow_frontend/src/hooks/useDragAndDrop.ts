import React, { useCallback } from 'react';
import { Node, ReactFlowInstance } from '@xyflow/react';
import { useToast } from '@chakra-ui/react';
import { SchemaFields, CalculationNodeData } from '../views/home/type';

// UploadedNode type (matches backend node structure)
interface UploadedNode {
  id: string;
  type: string;
  label: string;
  name?: string;
  description: string;
  category: string;
  file_name: string;
  schema: SchemaFields;
  nodeType?: string;
  color?: string;
}

interface UseDragAndDropParams {
  reactFlowInstance: React.MutableRefObject<ReactFlowInstance | null>;
  selectedProject: string | null;
  autoSaveEnabled: boolean;
  toast: ReturnType<typeof useToast>;
  uploadedNodes: any;
  setNodes: (updater: (nds: Node<CalculationNodeData>[]) => Node<CalculationNodeData>[]) => void;
  createNodeAPI: (nodeData: Node<CalculationNodeData>) => Promise<void>;
  handleRefreshNodeData: (filename: string) => Promise<any>;
  handleNodeUpdate: (nodeId: string, updatedData: Partial<CalculationNodeData>) => void;
}

export const useDragAndDrop = ({
  reactFlowInstance,
  selectedProject,
  autoSaveEnabled,
  toast,
  uploadedNodes,
  setNodes,
  createNodeAPI,
  handleRefreshNodeData,
  handleNodeUpdate,
}: UseDragAndDropParams) => {
  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();

      if (!reactFlowInstance.current) {
        console.log('ReactFlow instance not ready');
        return;
      }

      if (!selectedProject) {
        console.log('No project selected');
        toast({
          title: "No Project",
          description: "Please select a project first",
          status: "warning",
          duration: 2000,
          isClosable: true,
        });
        return;
      }

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const nodeDataString = event.dataTransfer.getData('application/nodedata');
      let nodeData;
      try {
        nodeData = JSON.parse(nodeDataString);
      } catch (error) {
        console.error('Invalid node data:', error);
        return;
      }

      if (!nodeData) {
        console.log('No node data received');
        return;
      }

      console.log('====================================');
      console.log('🔄 NEW DROP EVENT');
      console.log('Dropped nodeData:', nodeData);
      console.log('NodeData ID:', nodeData.id);
      console.log('NodeData Label:', nodeData.label);
      console.log('====================================');

      let schema: SchemaFields = {
        inputs: {},
        outputs: {},
        parameters: {},
        methods: {}
      };
      let nodeType = 'calculationNode';
      let label = nodeData.label || nodeData.name || 'New Calculator';
      let fileName: string = "";
      let categories = {};
      let color: string = nodeData.color;
      // Get the schema of the corresponding node from uploadedNodes
      if (uploadedNodes?.nodes && Array.isArray(uploadedNodes.nodes)) {
        console.log('Available nodes in uploadedNodes:', uploadedNodes.nodes.length);

        // Matching process
        let matchedNode: UploadedNode | null = null;

        // Attempt an exact match on the ID
        if (nodeData.id) {
          matchedNode = uploadedNodes.nodes.find((node: UploadedNode) => node.id === nodeData.id);
          if (matchedNode) {
            console.log('✅ Matched by ID:', nodeData.id);
          }
        }

        // If no match by ID, try by label
        if (!matchedNode && nodeData.label) {
          matchedNode = uploadedNodes.nodes.find((node: UploadedNode) => node.label === nodeData.label);
          if (matchedNode) {
            console.log('✅ Matched by label:', nodeData.label);
          }
        }

        // If that doesn't match, try by name
        if (!matchedNode && nodeData.name) {
          matchedNode = uploadedNodes.nodes.find((node: UploadedNode) => node.name === nodeData.name);
          if (matchedNode) {
            console.log('✅ Matched by name:', nodeData.name);
          }
        }

        if (matchedNode && matchedNode.schema) {
          console.log('📋 Processing schema for:', matchedNode.label);
          console.log('Original schema structure:', matchedNode.schema);

          // Get category
          categories = nodeData.categories;

          // Use the new structure schema as is
          schema = matchedNode.schema;

          // Check the contents of the schema
          const inputCount = schema.inputs ? Object.keys(schema.inputs).length : 0;
          const outputCount = schema.outputs ? Object.keys(schema.outputs).length : 0;
          const paramCount = schema.parameters ? Object.keys(schema.parameters).length : 0;
          const methodCount = schema.methods ? Object.keys(schema.methods).length : 0;

          console.log(`✅ Schema loaded: ${inputCount} inputs, ${outputCount} outputs, ${paramCount} parameters, ${methodCount} methods`);

          // If you need a default schema
          if (inputCount === 0 && outputCount === 0) {
            console.warn('⚠️ No ports found, using default schema');
            schema = {
              inputs: {
                "default_input": {
                  type: "any",
                  description: "Default input",
                }
              },
              outputs: {
                "default_output": {
                  type: "any",
                  description: "Default output",
                }
              },
              parameters: {},
              methods: {}
            };
          }

          // Get the correct label and type from matchedNode
          nodeType = matchedNode.category || matchedNode.nodeType || matchedNode.type || 'calculationNode';
          label = matchedNode.label || matchedNode.name || label;
          fileName = matchedNode.file_name || "";
          // add ".py"
          const chkPy = fileName.includes(".py");
          if (!chkPy) {
            fileName += ".py";
          }
        } else {
          console.log('❌ No matching node found, using fallback schema');
          // fallback schema
          schema = {
            inputs: {
              "input": {
                type: "any",
                description: "Input",
              }
            },
            outputs: {
              "output": {
                type: "any",
                description: "Output",
              }
            },
            parameters: {},
            methods: {}
          };
        }
      } else {
        console.warn('❌ uploadedNodes not available, using default schema');
      }

      // Generate new ID
      const newNodeId = `calc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      // Create a deep copy of the schema so that each node has independent parameter values
      const independentSchema = JSON.parse(JSON.stringify(schema));

      const newNode: Node<CalculationNodeData> = {
        id: newNodeId,
        type: nodeType,
        position,
        data: {
          file_name: fileName,
          label: label,
          instanceName: label,
          schema: independentSchema,
          nodeType: nodeType,
          nodeParameters: {},
          color: color,
        },
      };

      console.log('🎯 Creating NEW node:');
      console.log('Node data', newNode);
      console.log('  ID:', newNodeId);
      console.log('  Label:', label);
      console.log('  Schema:', schema);
      console.log(' file name:', fileName);
      console.log('====================================');

      // UI updates
      setNodes((nds) => {
        const updated = nds.concat(newNode);
        console.log('Total nodes after adding:', updated.length);
        return updated;
      });

      // Send to API
      if (autoSaveEnabled) {
        createNodeAPI(newNode);
      }

      // For workflow nodes, auto-refresh is skipped to preserve individual parameter values
      console.log('Skipping auto-refresh for workflow node to maintain independent parameters:', newNodeId);

      // Count calculation (supports new structure)
      const inputCount = schema.inputs ? Object.keys(schema.inputs).length : 0;
      const outputCount = schema.outputs ? Object.keys(schema.outputs).length : 0;

      toast({
        title: "Node Added",
        description: `"${label}" (${inputCount} inputs, ${outputCount} outputs)`,
        status: "success",
        duration: 2000,
        isClosable: true,
      });
    },
    [setNodes, toast, selectedProject, autoSaveEnabled, uploadedNodes, handleRefreshNodeData, handleNodeUpdate]
  );

  const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  return { onDrop, onDragOver };
};

export default useDragAndDrop;
