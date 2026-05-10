import Keycloak from "keycloak-js";

const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL || "";
const keycloakRealm = import.meta.env.VITE_KEYCLOAK_REALM || "neuroworkflow";
const keycloakClientId =
  import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "neuroworkflow-app";

if (!keycloakUrl || keycloakUrl.includes("<")) {
  console.error(
    "VITE_KEYCLOAK_URL is not configured. Authentication will fail."
  );
}

let _instance: Keycloak | null = null;

export function getKeycloak(): Keycloak {
  if (!_instance) {
    _instance = new Keycloak({
      url: keycloakUrl,
      realm: keycloakRealm,
      clientId: keycloakClientId,
    });
  }
  return _instance;
}

export function getAccountConsoleUrl(): string {
  return `${keycloakUrl.replace(/\/$/, "")}/realms/${keycloakRealm}/account`;
}

export function getKeycloakClientId(): string {
  return keycloakClientId;
}
