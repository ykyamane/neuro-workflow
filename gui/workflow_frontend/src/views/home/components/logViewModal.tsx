import { 
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Textarea,
  useDisclosure
} from "@chakra-ui/react";

interface LogViewProps {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  logText: string;
}

export default function LogViewModal({isOpen, onOpen, onClose, logText}: LogViewProps) {

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="6xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Workflow execution results</ModalHeader>

          <ModalBody>
            <Textarea
              value={logText}
              isReadOnly
              height="600px"
              size="sm"
            />
          </ModalBody>

          <ModalFooter>
            <Button onClick={onClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
