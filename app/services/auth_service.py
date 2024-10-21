# Set up constants for OAuth2
import webbrowser
from typing import List
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.config import oauth_settings
from app.logger import logger
from app.services.token_storage import DECODED_TOKEN

AUTHORITY = f"https://login.microsoftonline.com/{oauth_settings.AZURE_TENANT_ID}"
AUTH_URL = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"

# Role hierarchy mapping: which roles can fulfill which scopes
ROLE_HIERARCHY = {
    'Admin': ['Heroes.Read', 'Heroes.Create', 'Admin'],
    'Heroes.Create': ['Heroes.Read', 'Heroes.Create'],
    'Heroes.Read': ['Heroes.Read']
}

# OAuth2AuthorizationCodeBearer scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=AUTH_URL,
    tokenUrl=TOKEN_URL
)

# Prepare the parameters for the OAuth2 authorization URL
query_params = {
    "client_id": oauth_settings.AZURE_CLIENT_ID,
    "response_type": "code",
    "redirect_uri": oauth_settings.REDIRECT_URI,
    "scope": "api://6e1bf81c-ef36-40c4-b9f6-0853d397326a/Heroes.Create",
    "response_mode": "query"
}

# Encode the query parameters and construct the full authorization URL
login_url = f"https://login.microsoftonline.com/{oauth_settings.AZURE_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(query_params)} "

# Open the login URL in the default web browser
webbrowser.open_new_tab(login_url)  # This opens the login URL in a new browser tab


async def get_access_token(code: str):
    """Exchange authorization code for an access token."""

    logger.info("Starting authorization code exchange for access token")

    async with httpx.AsyncClient() as client:
        try:
            # Make the POST request to the token URL
            response = await client.post(
                TOKEN_URL,
                data={
                    'client_id': oauth_settings.AZURE_CLIENT_ID,
                    'client_secret': oauth_settings.AZURE_CLIENT_SECRET,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': oauth_settings.REDIRECT_URI,
                    'scope': oauth_settings.API_SCOPE,
                },
            )

            # Log the status of the token request response
            logger.info(f"Token endpoint responded with status code: {response.status_code}")

            # Parse the response JSON
            response_data = response.json()

            # Log the response data (be careful not to log sensitive information such as token directly)
            logger.info(f"Response data: {response_data}")

            # Check if the response contains an error
            if response.status_code != 200:
                logger.error(f"Failed to exchange code for token. Error: {response_data}")
                raise HTTPException(status_code=response.status_code, detail=response_data)

            # Log successful token retrieval
            access_token = response_data.get("access_token")
            logger.info(f"Access token received: {access_token[:10]}... (truncated for security)")

            return access_token

        except Exception as e:
            # Log any exceptions that occur during the process
            logger.exception(f"An error occurred during token exchange: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred during the token exchange process")


# Function to check if the token contains the required scopes, based on role hierarchy
def has_required_scope(token_scopes: List[str], required_scopes: List[str]) -> bool:
    """Check if any of the token's scopes fulfill the required scopes based on the role hierarchy."""
    logger.debug(f"Checking scopes: Token scopes: {token_scopes}, Required scopes: {required_scopes}")

    for token_scope in token_scopes:
        # Log which role (token scope) is being checked
        logger.debug(f"Checking token scope: {token_scope}")

        # Check if the token scope can fulfill the required scope using the role hierarchy
        for required_scope in required_scopes:
            if required_scope in ROLE_HIERARCHY.get(token_scope, []):
                logger.info(
                    f"Scope match: Token scope '{token_scope}' grants access to required scope '{required_scope}' "
                    f"based on the role hierarchy.")
                return True
            else:
                logger.debug(f"Token scope '{token_scope}' does not grant access to required scope '{required_scope}'.")

    # If no scopes satisfy the requirement, return False
    logger.warning(f"No token scopes match the required scopes: {required_scopes}")
    return False


# Dependency to validate that the user has the required scope
async def verify_scope(required_scopes: List[str]):
    logger.info("Starting scope verification")

    try:
        # Ensure there's a decoded token available for verification
        if DECODED_TOKEN is None:
            logger.error("No token stored for scope verification")
            raise HTTPException(status_code=401, detail="No token available for verification")

        # Extract the scopes from the stored decoded token (from 'scp' field)
        token_scopes = DECODED_TOKEN.get("scp", "").split()
        logger.debug(f"Token scopes extracted: {token_scopes}")
        logger.debug(f"Required scopes for operation: {required_scopes}")

        # Check if the token has the required scope based on role hierarchy
        if has_required_scope(token_scopes, required_scopes):
            logger.info(f"Scope verification successful. Token has the required scopes for the operation.")
            return DECODED_TOKEN
        else:
            logger.warning(f"Scope verification failed. Required: {required_scopes}, Found: {token_scopes}")
            raise HTTPException(status_code=403, detail="Insufficient scope for this operation")

    except Exception as e:
        logger.error(f"Error during scope verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify scope")
