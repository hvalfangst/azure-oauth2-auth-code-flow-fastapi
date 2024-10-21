# token_storage.py

# Global variable to hold the token and claims
from app.logger import logger

DECODED_TOKEN = None
ACCESS_TOKEN = None


def store_token(access_token: str, decoded_token: dict):
    global DECODED_TOKEN, ACCESS_TOKEN
    ACCESS_TOKEN = access_token
    DECODED_TOKEN = decoded_token
    logger.info("Access token and claims successfully stored")


def get_stored_token():
    return {"access_token": ACCESS_TOKEN, "claims": DECODED_TOKEN}
