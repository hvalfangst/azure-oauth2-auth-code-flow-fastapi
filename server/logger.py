# server/logger.py

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create a logger object that can be imported across the application
logger = logging.getLogger(__name__)
