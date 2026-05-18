import Keycloak from "keycloak-js";

const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL || "";
const keycloakRealm = import.meta.env.VITE_KEYCLOAK_REALM || "neuroworkflow";
const keycloakClientId =
  import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "neuroworkflow-app";

export const isKeycloakConfigured = Boolean(
  keycloakUrl && !keycloakUrl.includes("<")
);

if (!isKeycloakConfigured) {
  console.error(
    "VITE_KEYCLOAK_URL is not configured. Authentication will fail."
  );
}

declare global {
  interface Window {
    __NEURO_WORKFLOW_KEYCLOAK__?: Keycloak;
    __NEURO_WORKFLOW_KEYCLOAK_INIT__?: Promise<boolean>;
  }
}

export function getKeycloak(): Keycloak {
  if (!window.__NEURO_WORKFLOW_KEYCLOAK__) {
    window.__NEURO_WORKFLOW_KEYCLOAK__ = new Keycloak({
      url: keycloakUrl,
      realm: keycloakRealm,
      clientId: keycloakClientId,
    });
  }
  return window.__NEURO_WORKFLOW_KEYCLOAK__;
}

export function getAccountConsoleUrl(): string {
  return `${keycloakUrl.replace(/\/$/, "")}/realms/${keycloakRealm}/account`;
}

export function getKeycloakClientId(): string {
  return keycloakClientId;
}
