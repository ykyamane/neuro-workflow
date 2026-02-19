import { useEffect } from 'react';
import { Node, Edge } from '@xyflow/react';
import { useToast } from '@chakra-ui/react';
import { CalculationNodeData } from '../views/home/type';

interface UseKeyboardShortcutsParams {
  sharedNodes: Node<CalculationNodeData>[];
  sharedEdges: Edge[];
  setSharedNodes: (updater: Node<CalculationNodeData>[] | ((nds: Node<CalculationNodeData>[]) => Node<CalculationNodeData>[])) => void;
  setSharedEdges: (updater: Edge[] | ((eds: Edge[]) => Edge[])) => void;
  toast: ReturnType<typeof useToast>;
  autoSaveEnabled: boolean;
  isViewOpen: boolean;
  isCodeOpen: boolean;
  deleteEdgeAPI: (edgeId: string) => Promise<void>;
  deleteNodeAPI: (nodeId: string) => Promise<void>;
}

export const useKeyboardShortcuts = ({
  sharedNodes,
  sharedEdges,
  setSharedNodes,
  setSharedEdges,
  toast,
  autoSaveEnabled,
  isViewOpen,
  isCodeOpen,
  deleteEdgeAPI,
  deleteNodeAPI,
}: UseKeyboardShortcutsParams) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Disable deletion when modal is open
      if (isViewOpen || isCodeOpen) {
        return;
      }

      if (event.key === 'Delete' || event.key === 'Backspace') {
        const selectedEdges = sharedEdges.filter(edge => edge.selected);
        if (selectedEdges.length > 0) {
          event.preventDefault();
          if (autoSaveEnabled) {
            selectedEdges.forEach(edge => {
              deleteEdgeAPI(edge.id);
            });
          }
          setSharedEdges((eds: Edge[]) => eds.filter((edge: Edge) => !edge.selected));

          toast({
            title: "Deleted",
            description: `${selectedEdges.length} edge(s) deleted`,
            status: "info",
            duration: 2000,
            isClosable: true,
          });
        }

        const selectedNodes = sharedNodes.filter(node => node.selected);
        if (selectedNodes.length > 0) {
          event.preventDefault();
          const nodeIds = selectedNodes.map(node => node.id);

          if (autoSaveEnabled) {
            selectedNodes.forEach(node => {
              deleteNodeAPI(node.id);
            });

            const relatedEdges = sharedEdges.filter(
              (edge) => nodeIds.includes(edge.source) || nodeIds.includes(edge.target)
            );
            relatedEdges.forEach(edge => {
              deleteEdgeAPI(edge.id);
            });
          }

          setSharedNodes((nds: Node<CalculationNodeData>[]) => nds.filter((node: Node<CalculationNodeData>) => !node.selected));
          setSharedEdges((eds: Edge[]) => eds.filter(
            (edge: Edge) => !nodeIds.includes(edge.source) && !nodeIds.includes(edge.target)
          ));

          toast({
            title: "Deleted",
            description: `${selectedNodes.length} node(s) deleted`,
            status: "info",
            duration: 2000,
            isClosable: true,
          });
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [sharedNodes, sharedEdges, setSharedNodes, setSharedEdges, toast, autoSaveEnabled, isViewOpen, isCodeOpen]);
};

export default useKeyboardShortcuts;
