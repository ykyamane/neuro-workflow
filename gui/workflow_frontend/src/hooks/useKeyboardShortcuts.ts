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
  onRequestDeleteNodes: (nodeIds: string[]) => void;
  deleteEdgeAPI: (edgeId: string) => Promise<void>;
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
  onRequestDeleteNodes,
  deleteEdgeAPI,
}: UseKeyboardShortcutsParams) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isTypingTarget =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        Boolean(target?.isContentEditable);

      // Disable deletion when modal is open
      if (isViewOpen || isCodeOpen || isTypingTarget) {
        return;
      }

      if (event.key === 'Delete' || event.key === 'Backspace') {
        const selectedNodes = sharedNodes.filter(node => node.selected);
        if (selectedNodes.length > 0) {
          event.preventDefault();
          onRequestDeleteNodes(selectedNodes.map(node => node.id));
          return;
        }

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
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [sharedNodes, sharedEdges, setSharedNodes, setSharedEdges, toast, autoSaveEnabled, isViewOpen, isCodeOpen, onRequestDeleteNodes, deleteEdgeAPI]);
};

export default useKeyboardShortcuts;
