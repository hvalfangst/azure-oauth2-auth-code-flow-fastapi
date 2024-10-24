# client/config/oauth.py

from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic_settings import BaseSettings
from client import logger

load_dotenv()

class OAuthSettings(BaseSettings):
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_TENANT_ID: str
    API_SCOPE: str
    REDIRECT_URI: str

    class Config:
        env_file = ".env_oauth"


def initialize_oauth_settings():
    try:
        # Create an instance of OAuthSettings
        internal_oauth_settings = OAuthSettings()

        # Check if the required OAuth fields are set
        if not internal_oauth_settings.AZURE_CLIENT_ID or not internal_oauth_settings.AZURE_CLIENT_SECRET or not internal_oauth_settings.AZURE_TENANT_ID or not internal_oauth_settings.API_SCOPE:
            logger.logger.error("One or more required OAuth environment variables are missing.")
            raise HTTPException(status_code=500,
                                detail="Configuration error: Required OAuth environment variables are missing.")

        logger.logger.info("OAuth settings loaded successfully.")
        return internal_oauth_settings
    except FileNotFoundError:
        logger.logger.critical(".env file not found.")
        raise HTTPException(status_code=500, detail="Configuration error: .env file not found.")
    except Exception as e:
        logger.logger.critical(f"Error loading OAuth settings: {e}")
        raise HTTPException(status_code=500,
                            detail="Configuration error: An error occurred while loading OAuth settings.")


# Initialize OAuth settings
oauth_settings = initialize_oauth_settings()
