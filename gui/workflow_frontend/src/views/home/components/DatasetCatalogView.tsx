import React, { useCallback, useEffect, useState } from "react";
import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  FormControl,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  InputRightElement,
  Link,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Select,
  Spinner,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
  useDisclosure,
  useToast,
  Wrap,
  WrapItem,
} from "@chakra-ui/react";
import { SearchIcon } from "@chakra-ui/icons";
import {
  CatalogDataset,
  CatalogSource,
  CatalogStatusResponse,
  fetchCatalogDataset,
  fetchCatalogStatus,
  searchCatalog,
  syncCatalog,
} from "../../../api/catalogApi";

const SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All sources" },
  { value: "dandi", label: "DANDI" },
  { value: "cbs", label: "CBS" },
  { value: "brainminds", label: "Brain/MINDS" },
  { value: "bmb_human", label: "BMB Human" },
  { value: "aws", label: "AWS (SRPBS TS)" },
];

const sourceColor = (source: string): string => {
  switch (source) {
    case "dandi":
      return "purple";
    case "cbs":
      return "blue";
    case "brainminds":
      return "green";
    case "bmb_human":
      return "teal";
    case "aws":
      return "orange";
    default:
      return "gray";
  }
};

const formatBytes = (bytes?: number): string => {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
};

const DatasetCatalogView: React.FC = () => {
  const toast = useToast();
  const detailModal = useDisclosure();

  const [status, setStatus] = useState<CatalogStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("");
  const [results, setResults] = useState<CatalogDataset[]>([]);
  const [searching, setSearching] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [selected, setSelected] = useState<CatalogDataset | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const data = await fetchCatalogStatus();
      setStatus(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load status";
      setStatus({ mdb_available: false, error: message });
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const runSearch = async () => {
    const trimmed = query.trim();
    if (!trimmed) {
      toast({
        title: "Enter a search query",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setSearching(true);
    try {
      const data = await searchCatalog(
        trimmed,
        source ? (source as CatalogSource) : undefined
      );
      setResults(data.datasets);
      setLastQuery(trimmed);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      toast({
        title: "Search failed",
        description: message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSearching(false);
    }
  };

  const handleSync = async () => {
    if (
      !window.confirm(
        "Sync all external catalogs via mdb? This may take several minutes."
      )
    ) {
      return;
    }

    setSyncing(true);
    try {
      await syncCatalog();
      toast({
        title: "Sync started",
        description: "mdb catalog sync completed.",
        status: "success",
        duration: 4000,
        isClosable: true,
      });
      await loadStatus();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Sync failed";
      toast({
        title: "Sync failed",
        description: message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSyncing(false);
    }
  };

  const openDetail = async (dataset: CatalogDataset) => {
    setSelected(dataset);
    detailModal.onOpen();
    setDetailLoading(true);
    try {
      const full = await fetchCatalogDataset(dataset.source, dataset.dataset_id);
      setSelected(full);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load details";
      toast({
        title: "Could not load dataset details",
        description: message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setDetailLoading(false);
    }
  };

  const copyUrl = (url: string) => {
    const value = url.trim();
    if (!value) {
      toast({
        title: "No download URL",
        status: "warning",
        duration: 2000,
        isClosable: true,
      });
      return;
    }

    const syncCopy = (): boolean => {
      const textarea = document.createElement("textarea");
      textarea.value = value;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.top = "0";
      textarea.style.left = "0";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      textarea.setSelectionRange(0, value.length);
      let copied = false;
      try {
        copied = document.execCommand("copy");
      } catch {
        copied = false;
      }
      document.body.removeChild(textarea);
      return copied;
    };

    if (syncCopy()) {
      toast({
        title: "Download URL copied",
        status: "success",
        duration: 2000,
        isClosable: true,
      });
      return;
    }

    if (window.isSecureContext && navigator.clipboard?.writeText) {
      void navigator.clipboard.writeText(value).then(
        () => {
          toast({
            title: "Download URL copied",
            status: "success",
            duration: 2000,
            isClosable: true,
          });
        },
        () => {
          toast({
            title: "Copy failed",
            description: value,
            status: "error",
            duration: 5000,
            isClosable: true,
          });
        }
      );
      return;
    }

    toast({
      title: "Copy failed",
      description: value,
      status: "error",
      duration: 5000,
      isClosable: true,
    });
  };

  return (
    <Box p={4} maxW="1200px" mx="auto">
      <VStack align="stretch" spacing={6}>
        <Box>
          <Text fontSize="2xl" fontWeight="bold">
            Dataset Catalog
          </Text>
          <Text fontSize="sm" color="gray.500" mt={1}>
            Search neuroscience datasets synced from DANDI, CBS, and Brain/MINDS via
            mdb.
          </Text>
        </Box>

        {statusLoading ? (
          <HStack>
            <Spinner size="sm" />
            <Text fontSize="sm">Loading mdb status...</Text>
          </HStack>
        ) : status?.mdb_available ? (
          <Wrap spacing={2}>
            <WrapItem>
              <Badge colorScheme="green">mdb connected</Badge>
            </WrapItem>
            {status.statistics?.total_datasets != null && (
              <WrapItem>
                <Badge>{status.statistics.total_datasets} datasets</Badge>
              </WrapItem>
            )}
            {Object.entries(status.statistics?.source_counts || {}).map(
              ([key, count]) => (
                <WrapItem key={key}>
                  <Badge colorScheme={sourceColor(key)} variant="subtle">
                    {key}: {count}
                  </Badge>
                </WrapItem>
              )
            )}
          </Wrap>
        ) : (
          <Alert status="warning">
            <AlertIcon />
            mdb is unavailable. Start mdb on the host (port 8004) and check
            MDB_BASE_URL in the backend.
            {status?.error ? ` (${status.error})` : ""}
          </Alert>
        )}

        <HStack align="flex-end" flexWrap="wrap" spacing={4}>
          <FormControl flex="2" minW="240px">
            <FormLabel>Search</FormLabel>
            <InputGroup>
              <Input
                placeholder="e.g. hippocampus, marmoset, electrophysiology"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") runSearch();
                }}
              />
              <InputRightElement width="3rem">
                <Button
                  h="1.75rem"
                  size="sm"
                  onClick={runSearch}
                  isLoading={searching}
                  aria-label="Search"
                >
                  <SearchIcon />
                </Button>
              </InputRightElement>
            </InputGroup>
          </FormControl>

          <FormControl flex="1" minW="160px">
            <FormLabel>Source</FormLabel>
            <Select
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              {SOURCE_OPTIONS.map((opt) => (
                <option key={opt.value || "all"} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </FormControl>

          <Button
            colorScheme="blue"
            onClick={runSearch}
            isLoading={searching}
            loadingText="Searching"
          >
            Search
          </Button>

          <Button
            variant="outline"
            onClick={handleSync}
            isLoading={syncing}
            loadingText="Syncing"
          >
            Sync catalogs
          </Button>
        </HStack>

        {lastQuery && (
          <Text fontSize="sm" color="gray.500">
            {results.length} result(s) for &quot;{lastQuery}&quot;
            {source ? ` in ${source}` : ""}
          </Text>
        )}

        {searching ? (
          <Box textAlign="center" py={8}>
            <Spinner />
            <Text mt={2}>Searching...</Text>
          </Box>
        ) : results.length > 0 ? (
          <TableContainer borderWidth="1px" borderRadius="md">
            <Table size="sm">
              <Thead>
                <Tr>
                  <Th>Source</Th>
                  <Th>ID</Th>
                  <Th>Name</Th>
                  <Th isNumeric>Data URLs</Th>
                  <Th>Synced</Th>
                </Tr>
              </Thead>
              <Tbody>
                {results.map((dataset) => (
                  <Tr
                    key={`${dataset.source}-${dataset.dataset_id}`}
                    _hover={{ bg: "gray.50", _dark: { bg: "whiteAlpha.100" } }}
                    cursor="pointer"
                    onClick={() => openDetail(dataset)}
                  >
                    <Td>
                      <Badge colorScheme={sourceColor(dataset.source)}>
                        {dataset.source}
                      </Badge>
                    </Td>
                    <Td fontFamily="mono" fontSize="xs">
                      {dataset.dataset_id}
                    </Td>
                    <Td maxW="420px" isTruncated title={dataset.name}>
                      {dataset.name || "—"}
                    </Td>
                    <Td isNumeric>
                      {dataset.data_url_count}
                      {dataset.data_url_total != null &&
                      dataset.data_url_total > dataset.data_url_count
                        ? ` / ${dataset.data_url_total}`
                        : ""}
                      {dataset.truncated ? " *" : ""}
                    </Td>
                    <Td fontSize="xs" whiteSpace="nowrap">
                      {dataset.synced_at || "—"}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        ) : lastQuery ? (
          <Text color="gray.500">No datasets found.</Text>
        ) : null}
      </VStack>

      <Modal
        isOpen={detailModal.isOpen}
        onClose={detailModal.onClose}
        size="xl"
        scrollBehavior="inside"
      >
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {selected?.name || selected?.dataset_id || "Dataset"}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selected && (
              <VStack align="stretch" spacing={4}>
                <HStack flexWrap="wrap">
                  <Badge colorScheme={sourceColor(selected.source)}>
                    {selected.source}
                  </Badge>
                  <Text fontFamily="mono" fontSize="sm">
                    {selected.dataset_id}
                  </Text>
                </HStack>

                {selected.description ? (
                  <Text fontSize="sm">{selected.description}</Text>
                ) : null}

                {selected.landing_page ? (
                  <Link
                    href={selected.landing_page}
                    isExternal
                    fontSize="sm"
                    color="blue.600"
                  >
                    Open dataset portal
                  </Link>
                ) : null}

                <Text fontSize="sm" color="gray.500">
                  Data files: {selected.data_url_count}
                  {selected.data_url_total != null
                    ? ` / ${selected.data_url_total} total`
                    : ""}
                  {selected.truncated ? " (truncated in mdb)" : ""}
                  {" · "}
                  Copy download URL for workflow nodes; use Portal to browse in browser.
                </Text>

                {detailLoading ? (
                  <HStack justify="center" py={4}>
                    <Spinner size="sm" />
                    <Text fontSize="sm">Loading file URLs...</Text>
                  </HStack>
                ) : selected.data_urls && selected.data_urls.length > 0 ? (
                  <TableContainer borderWidth="1px" borderRadius="md">
                    <Table size="sm">
                      <Thead>
                        <Tr>
                          <Th>Label</Th>
                          <Th isNumeric>Size</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {selected.data_urls.map((item, index) => {
                          const portalUrl =
                            item.browse_url || selected.landing_page;
                          const label =
                            item.label || item.path || item.url || "file";
                          return (
                            <Tr key={`${item.url}-${index}`}>
                              <Td
                                fontSize="xs"
                                maxW="360px"
                                isTruncated
                                title={label}
                              >
                                {portalUrl ? (
                                  <Link href={portalUrl} isExternal color="blue.600">
                                    {label}
                                  </Link>
                                ) : (
                                  label
                                )}
                              </Td>
                              <Td isNumeric fontSize="xs">
                                {formatBytes(item.size)}
                              </Td>
                              <Td>
                                <HStack spacing={2}>
                                  {portalUrl ? (
                                    <Button
                                      size="xs"
                                      variant="outline"
                                      as="a"
                                      href={portalUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      Portal
                                    </Button>
                                  ) : null}
                                  <Button
                                    size="xs"
                                    variant="outline"
                                    onClick={() => copyUrl(item.url)}
                                  >
                                    Copy download URL
                                  </Button>
                                </HStack>
                              </Td>
                            </Tr>
                          );
                        })}
                      </Tbody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Text fontSize="sm" color="gray.500">
                    No download URLs in metadata.
                  </Text>
                )}
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default DatasetCatalogView;
