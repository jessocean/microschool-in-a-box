import uvicorn
import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server.log")
    ]
)

logger = logging.getLogger("weight-management-server")

def run_server():
    """Run the FastAPI server with proper error handling"""
    try:
        logger.info("Starting Weight Management API server...")
        
        # Check if the required modules are installed
        try:
            import fastapi
            import networkx
            import numpy
            import matplotlib
            logger.info("All required modules are installed")
        except ImportError as e:
            logger.error(f"Missing required module: {e}")
            logger.error("Please install all required modules using: pip install -r requirements.txt")
            return
        
        # Run the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return

if __name__ == "__main__":
    run_server() 