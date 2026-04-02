import Keycloak from "keycloak-js";

const keycloakUrl = import.meta.env.VITE_KEYCLOAK_URL || "";
const keycloakRealm = import.meta.env.VITE_KEYCLOAK_REALM || "neuroworkflow";
const keycloakClientId =
  import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "neuroworkflow-app";

export const isKeycloakConfigured = Boolean(
  keycloakUrl && !keycloakUrl.includes("<")
);

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
