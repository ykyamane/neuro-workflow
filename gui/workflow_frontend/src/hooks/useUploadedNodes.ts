import { SchemaFields } from "../views/home/type";
import { useState, useEffect, useCallback } from "react";

// Backend response type definition
interface UploadedNodesResponse {
  categories: any;
  nodes: BackendNodeType[];
  total_files: number;
  total_nodes: number;
}

interface BackendNodeType {
  id: string;
  type: string;
  label: string;
  description: string;
  category: string;
  file_id: string;
  class_name: string;
  file_name: string;
  schema: SchemaFields;
  color: string;
}

// interface SchemaField {
//   title: string;
//   type: string;
//   description: string;
//   port_direction: "input" | "output" | "parameter";
//   default_value?: string;
// }

interface UseUploadedNodesReturn {
  data: UploadedNodesResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * A custom hook to get the list of uploaded nodes
 */
export const useUploadedNodes = (): UseUploadedNodesReturn => {
  const [data, setData] = useState<UploadedNodesResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUploadedNodes = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch("/api/box/uploaded-nodes/");

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: UploadedNodesResponse = await response.json();

      console.log("This is response data", result);

      setData(result);
    } catch (err) {
      console.error("Failed to fetch uploaded nodes:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch nodes");
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUploadedNodes();
  }, [fetchUploadedNodes]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchUploadedNodes,
  };
};



/**
 * Python custom hook to get file list
 */
interface PythonFile {
  id: string;
  name: string;
  description: string;
  file: string;
  uploaded_by: string | null;
  uploaded_by_name: string | null;
  file_size: number;
  is_analyzed: boolean;
  analysis_error: string | null;
  node_classes_count: number;
  created_at: string;
  updated_at: string;
}

interface UsePythonFilesReturn {
  files: PythonFile[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  deleteFile: (id: string) => Promise<boolean>;
}

export const usePythonFiles = (params?: {
  name?: string;
  analyzed_only?: boolean;
}): UsePythonFilesReturn => {
  const [files, setFiles] = useState<PythonFile[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPythonFiles = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Build query parameters
      const searchParams = new URLSearchParams();
      if (params?.name) {
        searchParams.append("name", params.name);
      }
      if (params?.analyzed_only) {
        searchParams.append("analyzed_only", "true");
      }

      const url = `/api/box/files/${
        searchParams.toString() ? `?${searchParams.toString()}` : ""
      }`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: PythonFile[] = await response.json();
      setFiles(result);
    } catch (err) {
      console.error("Failed to fetch Python files:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch files");
      setFiles([]);
    } finally {
      setIsLoading(false);
    }
  }, [params?.name, params?.analyzed_only]);

  const deleteFile = useCallback(async (id: string): Promise<boolean> => {
    try {
      const response = await fetch(`/api/box/files/${id}/`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Failed to delete file: ${response.status}`);
      }

      // Remove from file list
      setFiles((prev) => prev.filter((file) => file.id !== id));
      return true;
    } catch (err) {
      console.error("Failed to delete file:", err);
      setError(err instanceof Error ? err.message : "Failed to delete file");
      return false;
    }
  }, []);

  useEffect(() => {
    fetchPythonFiles();
  }, [fetchPythonFiles]);

  return {
    files,
    isLoading,
    error,
    refetch: fetchPythonFiles,
    deleteFile,
  };
};
