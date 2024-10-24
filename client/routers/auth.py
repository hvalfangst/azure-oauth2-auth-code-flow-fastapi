# client/routers/auth.py

from http.client import HTTPException
from fastapi import APIRouter, HTTPException, Request
from client.logger import logger
from client.services.auth_service import handle_openid_connect_flow

router = APIRouter()


# Example usage in the callback route
@router.get("/callback")
async def auth_callback(request: Request):
    """Callback handler for OpenID Connect flow."""
    logger.info("Received callback request on /auth/callback")

    # Extract the authorization code from the query params
    code = request.query_params.get("code")

    if not code:
        logger.error("Authorization code not found in the request query parameters")
        raise HTTPException(status_code=400, detail="Authorization code not found")

    # Call the OpenID Connect handler function
    try:
        logger.info("Initiating OpenID Connect flow handling")
        result = await handle_openid_connect_flow(code)
        logger.info("OpenID Connect flow completed successfully")
        return result
    except Exception as e:
        logger.error(f"An error occurred during OpenID Connect flow: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during OpenID Connect flow")