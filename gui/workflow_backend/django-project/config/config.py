from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "db")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080/auth")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "neuroworkflow")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "neuroworkflow-app")
# Optional. Override expected `iss` claim when the browser-facing Keycloak URL
# differs from KEYCLOAK_URL (used for JWKS fetch). Leave unset for single-host
# setups.
KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
