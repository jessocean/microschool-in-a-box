import uvicorn
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("production.log")
    ]
)

logger = logging.getLogger("weight-management-production")

def run_production_server():
    """Run the FastAPI server in production mode"""
    try:
        logger.info("Starting Weight Management API server in production mode...")
        
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
        
        # Check if ANTHROPIC_API_KEY is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.warning("ANTHROPIC_API_KEY environment variable not set. Claude integration will not work.")
        
        # Get port from environment variable or use default
        port = int(os.environ.get("PORT", 8000))
        
        # Run the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Disable reload in production
            log_level="info",
            workers=4  # Use multiple workers in production
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return

if __name__ == "__main__":
    run_production_server() 