#!/usr/bin/env bash
#
# Import the NeuroWorkflow realm into a running Keycloak instance.
#
# Usage:
#   ./setup.sh                          # defaults: admin/admin @ http://localhost:8080
#   KEYCLOAK_ADMIN_PASSWORD=secret ./setup.sh
#
# Prerequisites:
#   - Keycloak container is running and healthy
#   - curl is installed
#
set -euo pipefail

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080/auth}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
REALM_FILE="$(dirname "$0")/realm-export.json"

echo "Waiting for Keycloak at ${KEYCLOAK_URL} ..."
for i in $(seq 1 30); do
  if curl -sf "${KEYCLOAK_URL}/realms/master" > /dev/null 2>&1; then
    echo "Keycloak is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: Keycloak not reachable after 30 attempts." >&2
    exit 1
  fi
  sleep 2
done

echo "Obtaining admin token ..."
TOKEN=$(curl -sf -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli" \
  -d "username=${ADMIN_USER}" \
  -d "password=${ADMIN_PASS}" \
  -d "grant_type=password" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Checking if realm 'neuroworkflow' already exists ..."
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "${KEYCLOAK_URL}/admin/realms/neuroworkflow" || true)

if [ "$STATUS" = "200" ]; then
  echo "Realm 'neuroworkflow' already exists — skipping import."
  echo "To re-import, delete the realm first via the Keycloak admin console."
else
  echo "Importing realm from ${REALM_FILE} ..."
  curl -sf -X POST "${KEYCLOAK_URL}/admin/realms" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${REALM_FILE}"
  echo "Realm 'neuroworkflow' imported successfully."
fi

echo ""
echo "Done. You can now access Keycloak at:"
echo "  Admin console: ${KEYCLOAK_URL}/admin/"
echo "  Account page:  ${KEYCLOAK_URL}/realms/neuroworkflow/account/"
