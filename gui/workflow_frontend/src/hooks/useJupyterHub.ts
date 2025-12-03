import { useState, useCallback } from "react";
import { useToast } from "@chakra-ui/react";

interface JupyterHubConfig {
  baseUrl: string;
  apiEndpoint: string;
  isDevelopment?: boolean;
  jwtToken?: string; // JWT tokens for production environments
}

interface JupyterSession {
  projectId: string;
  url: string;
  status: "starting" | "ready" | "error";
  error?: string;
}

interface UseJupyterHubReturn {
  launchJupyter: (projectId: string) => Promise<string | null>;
  isLoading: (projectId: string) => boolean;
  isReady: (projectId: string) => boolean;
  getUrl: (projectId: string) => string | null;
  getError: (projectId: string) => string | null;
  closeSession: (projectId: string) => void;
  sessions: Record<string, JupyterSession>;
}

const useJupyterHub = (
  config: JupyterHubConfig = {
    baseUrl: "http://localhost:8000",
    apiEndpoint: "/api/jupyterhub",
    isDevelopment: true, // Default is development mode
  }
): UseJupyterHubReturn => {
  const toast = useToast();
  const [sessions, setSessions] = useState<Record<string, JupyterSession>>({});

  // Launch a JupyterHub session
  const launchJupyter = useCallback(
    async (projectId: string): Promise<string | null> => {
      try {
        // If there is an existing session, return its URL.
        if (sessions[projectId]?.status === "ready") {
          console.log(`Project ${projectId} session already exists`);
          return sessions[projectId].url;
        }

        // Update session state
        setSessions((prev) => ({
          ...prev,
          [projectId]: {
            projectId,
            url: "",
            status: "starting",
          },
        }));

        let jupyterUrl: string;

        if (config.isDevelopment) {
          // Development mode: Directly access the URL containing the project ID
          jupyterUrl = `${config.baseUrl}/project/${projectId}`;

          console.log(`Development mode: Accessing ${jupyterUrl}`);

          // Development mode only supports simple standby
          await new Promise((resolve) => setTimeout(resolve, 1000));
        } else {
          // Production mode: JWT authentication through the Django API
          const requestBody: any = {
            project_id: projectId,
          };

          // Add JWT token if set
          if (config.jwtToken) {
            requestBody.token = config.jwtToken;
          }

          const response = await fetch(`${config.apiEndpoint}/launch/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              // The JWT token is also included in the Authorization header.
              ...(config.jwtToken && {
                Authorization: `Bearer ${config.jwtToken}`,
              }),
            },
            credentials: "include",
            body: JSON.stringify(requestBody),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(
              errorData.error ||
                `HTTP ${response.status}: Failed to launch JupyterHub`
            );
          }

          const data = await response.json();

          // Use a URL containing the project ID even in production
          jupyterUrl =
            data.jupyterhub_url || `${config.baseUrl}/project/${projectId}`;

          // If there is a token, add it to the URL (for iframes)
          if (config.jwtToken && !data.jupyterhub_url) {
            jupyterUrl += `?token=${config.jwtToken}`;
          }

          // Wait for JupyterHub to be ready
          await waitForJupyterReady(config.baseUrl, projectId);
        }

        // Update the session state to completed
        setSessions((prev) => ({
          ...prev,
          [projectId]: {
            projectId,
            url: jupyterUrl,
            status: "ready",
          },
        }));

        toast({
          title: "JupyterLab Ready",
          description: config.isDevelopment
            ? `development mode: Project "${projectId}" JupyterLab has started`
            : `Project "${projectId}" JupyterLab has started`,
          status: "success",
          duration: 3000,
          isClosable: true,
        });

        return jupyterUrl;
      } catch (error) {
        console.error("JupyterHub launch error:", error);

        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";

        // Update session state to error
        setSessions((prev) => ({
          ...prev,
          [projectId]: {
            projectId,
            url: "",
            status: "error",
            error: errorMessage,
          },
        }));

        toast({
          title: "JupyterHub startup error",
          description: errorMessage,
          status: "error",
          duration: 5000,
          isClosable: true,
        });

        return null;
      }
    },
    [config, toast, sessions]
  );

  // Wait for JupyterHub to be ready
  const waitForJupyterReady = async (
    baseUrl: string,
    projectId: string,
    maxAttempts = 20
  ): Promise<void> => {
    console.log(
      `Waiting for JupyterHub to be ready for project ${projectId}...`
    );

    for (let i = 0; i < maxAttempts; i++) {
      try {
        // Check the health check endpoint
        // Consider the path when using a named server
        const healthCheckUrl = `${baseUrl}/hub/api`;

        // Send a fetch request
        await fetch(healthCheckUrl, {
          method: "HEAD",
          mode: "no-cors",
          cache: "no-cache",
        });

        // Minimum waiting time (3 seconds)
        if (i >= 2) {
          console.log(`JupyterHub is ready for project ${projectId}`);
          return;
        }
      } catch (error) {
        // Errors are expected (CORS, etc.) so ignore them
      }

      // 1秒待機
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    // Continue even if timeout occurs (this is actually confirmed in an iframe)
    console.warn("JupyterHub health check timed out, but continuing...");
  };

  // Session status check helper function
  const isLoading = useCallback(
    (projectId: string): boolean => {
      return sessions[projectId]?.status === "starting";
    },
    [sessions]
  );

  const isReady = useCallback(
    (projectId: string): boolean => {
      return sessions[projectId]?.status === "ready";
    },
    [sessions]
  );

  const getUrl = useCallback(
    (projectId: string): string | null => {
      const session = sessions[projectId];
      return session?.status === "ready" ? session.url : null;
    },
    [sessions]
  );

  const getError = useCallback(
    (projectId: string): string | null => {
      const session = sessions[projectId];
      return session?.status === "error"
        ? session.error || "Unknown error"
        : null;
    },
    [sessions]
  );

  // Close session
  const closeSession = useCallback(
    (projectId: string) => {
      console.log(`Closing session for project ${projectId}`);

      setSessions((prev) => {
        const newSessions = { ...prev };
        delete newSessions[projectId];
        return newSessions;
      });

      toast({
        title: "Session ends",
        description: `Project "${projectId}" finished session`,
        status: "info",
        duration: 2000,
        isClosable: true,
      });
    },
    [toast]
  );

  return {
    launchJupyter,
    isLoading,
    isReady,
    getUrl,
    getError,
    closeSession,
    sessions, // Session information is also published for debugging purposes.
  };
};

export default useJupyterHub;
