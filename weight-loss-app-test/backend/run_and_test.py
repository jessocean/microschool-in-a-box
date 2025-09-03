import subprocess
import threading
import time
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("run-and-test")

def run_server():
    """Run the FastAPI server"""
    logger.info("Starting FastAPI server...")
    try:
        # Run the server
        subprocess.run(["py", "run_server.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running server: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    return True

def run_tests():
    """Run the API tests"""
    logger.info("Running API tests...")
    try:
        # Run the tests
        subprocess.run(["py", "test_api.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running tests: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    return True

def main():
    """Run the server and tests"""
    # Check if the required modules are installed
    try:
        import fastapi
        import networkx
        import numpy
        import matplotlib
        import requests
        logger.info("All required modules are installed")
    except ImportError as e:
        logger.error(f"Missing required module: {e}")
        logger.error("Please install all required modules using: pip install -r requirements.txt")
        return
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for the server to start
    logger.info("Waiting for server to start...")
    time.sleep(5)
    
    # Run the tests
    success = run_tests()
    
    if success:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 