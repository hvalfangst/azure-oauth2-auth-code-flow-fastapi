# client/services/auth_service.py

# Set up constants for OAuth2
import webbrowser
from typing import List
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

from client.config import oauth_settings
from client.logger import logger
from client.services.token_storage import DECODED_TOKEN

AUTHORITY = f"https://login.microsoftonline.com/{oauth_settings.AZURE_TENANT_ID}"
AUTH_URL = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
JWKS_URL = f"https://login.microsoftonline.com/{oauth_settings.AZURE_TENANT_ID}/discovery/v2.0/keys"

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
    "scope": "openid profile email User.Read",
    "response_mode": "query"
}

# Encode the query parameters and construct the full authorization URL
login_url = f"https://login.microsoftonline.com/{oauth_settings.AZURE_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(query_params)} "

# Open the login URL in the default web browser
webbrowser.open_new_tab(login_url)  # This opens the login URL in a new browser tab


async def handle_openid_connect_flow(code: str):
    """
    Handle OpenID Connect flow by exchanging the authorization code for tokens,
    decoding the ID token, and verifying the token.
    """
    # Exchange the authorization code for access and ID tokens
    try:
        logger.info("Attempting to request access token")
        token = await get_access_token(code)  # Function that exchanges code for token
        logger.info("Attempting to fetch id_token from token")
        id_token = token.get("id_token")
        logger.info("Attempting to fetch access_token from token")
        access_token = token.get("access_token")

        if not id_token:
            raise HTTPException(status_code=400, detail="ID token not found in response")

        # Decode the ID token without verifying the signature first
        decoded_id_token = jwt.decode(id_token, options={"verify_signature": False}, algorithms=["RS256"])
        print("Decoded ID Token:", decoded_id_token)

        # Decode the access token without verifying the signature first
        decoded_access_token = jwt.decode(access_token, options={"verify_signature": False}, algorithms=["RS256"])
        print("Decoded access Token:", decoded_access_token)

        # Verify the ID token signature and its claims
        # verified_token = await verify_id_token(id_token)
        # print("Verified ID Token:", verified_token)

        return {
            "access_token": decoded_access_token,
            "id_token": decoded_id_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


async def verify_id_token(id_token: str):
    """
    Verify the ID token using the JWKS from the Microsoft Identity platform.
    """
    logger.info("Starting ID token verification.")

    try:
        # Fetch the JWKS (JSON Web Key Set) asynchronously from the provider
        logger.info("Fetching JWKS from %s", JWKS_URL)
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()  # Raise an exception for HTTP errors
            jwks = response.json()
            logger.info("Successfully fetched JWKS: %s", jwks)  # Log the JWKS data (consider redacting sensitive info)

        # Get the public key ID from the token header
        logger.info("Extracting 'kid' from the token header.")
        kid = jwt.get_unverified_header(id_token)["kid"]
        logger.info("Public key ID (kid): %s", kid)

        # Find the corresponding public key in the JWKS
        logger.info("Searching for matching key in JWKS.")
        rsa_key = next(key for key in jwks["keys"] if key["kid"] == kid)
        logger.info("Found matching key for kid: %s", kid)

        # Use the RSA public key to verify the token's signature and validate claims
        logger.info("Verifying the ID token signature and validating claims.")
        verified_token = jwt.decode(id_token, rsa_key, algorithms=["RS256"], audience=oauth_settings.AZURE_CLIENT_ID)
        logger.info("ID token verified successfully.")

        return verified_token

    except jwt.ExpiredSignatureError:
        logger.error("ID token has expired.")
        raise HTTPException(status_code=403, detail="ID token has expired.")
    except jwt.JWTClaimsError as claims_error:
        logger.error("Invalid claims in ID token: %s", claims_error)
        raise HTTPException(status_code=403, detail="Invalid claims in ID token.")
    except httpx.HTTPStatusError as http_error:
        logger.error("HTTP error while fetching JWKS: %s", http_error)
        raise HTTPException(status_code=403, detail="Could not validate credentials.")
    except Exception as e:
        logger.error("An unexpected error occurred during ID token verification: %s", str(e))
        raise HTTPException(status_code=403, detail="Could not validate credentials.")


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

            logger.info(f"Response data: {response_data}")

            # Check if the response contains an error
            if response.status_code != 200:
                logger.error(f"Failed to exchange code for token. Error: {response_data}")
                raise HTTPException(status_code=response.status_code, detail=response_data)

            return response_data

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
