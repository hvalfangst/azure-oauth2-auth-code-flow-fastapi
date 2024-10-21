from http.client import HTTPException

import httpx
import jwt
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request

from app.config import oauth_settings
from app.logger import logger
from app.services.auth_service import get_access_token
from app.services.token_storage import store_token

router = APIRouter()


# Fetch Microsoft's JWKS keys (replace with your tenant's actual URL)
JWKS_URL = f"https://login.microsoftonline.com/{oauth_settings.AZURE_TENANT_ID}/discovery/v2.0/keys"


# Fetch the JWKS from Microsoft
async def fetch_jwks():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            return response.json()["keys"]

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while fetching JWKS: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to fetch JWKS: {e.response.text}")
    except Exception as e:
        logger.error(f"Error fetching JWKS: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch public keys for JWT verification")


# Function to get the public key from the JWKS
def get_public_key(jwks, kid):
    for key in jwks:
        if key["kid"] == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    raise HTTPException(status_code=400, detail="Invalid token: Public key not found")


# Function to handle the authorization code callback
@router.get("/callback")
async def auth_callback(request: Request):
    """Handle the callback from Microsoft after user authorization."""
    logger.info("Received request on /callback endpoint")

    # Extract the 'code' query parameter from the request
    code = request.query_params.get("code")

    if not code:
        logger.error("Authorization code not found in the query parameters")
        raise HTTPException(status_code=400, detail="Authorization code not found")

    logger.info(f"Authorization Code:\n\n [{code}]\n")

    # Exchange the authorization code for access token
    try:
        logger.info("Attempting to exchange authorization code for access token")
        token = await get_access_token(code)
        logger.info(
            f"Access token successfully received: [{token[:10]}...]")  # Log only first few characters for security

        # Decode the access token (without verifying signature for now)
        logger.info("Decoding the access token to extract claims...")
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False}, algorithms=["RS256"])
            logger.info(f"Decoded Token Claims: {decoded_token}")

            # Store the access token and decoded claims in the common file
            store_token(token, decoded_token)

            return {
                "access_token": token,
                "claims": decoded_token
            }

        except jwt.PyJWTError as jwt_error:
            logger.error(f"Error decoding JWT token: {jwt_error}")
            raise HTTPException(status_code=500, detail="Failed to decode token claims")

    except HTTPException as e:
        logger.error(f"Failed to exchange code for token. Error: [{str(e.detail)}]")
        return {"error": str(e.detail)}

    except Exception as e:
        logger.exception("An unexpected error occurred while handling the token exchange")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
