import subprocess
import logging
import sys
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("run-all-tests")

def run_test(test_name, test_script):
    """Run a test script and return success status"""
    logger.info(f"Running {test_name}...")
    try:
        subprocess.run(["py", test_script], check=True)
        logger.info(f"{test_name} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {test_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in {test_name}: {e}")
        return False

def main():
    """Run all tests"""
    # Check if the required modules are installed
    try:
        import fastapi
        import networkx
        import numpy
        import matplotlib
        import requests
        import anthropic
        logger.info("All required modules are installed")
    except ImportError as e:
        logger.error(f"Missing required module: {e}")
        logger.error("Please install all required modules using: pip install -r requirements.txt")
        return
    
    # Check if ANTHROPIC_API_KEY is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY environment variable not set. Some tests may fail.")
    
    # Run network model test
    network_success = run_test("Network Model Test", "test_network.py")
    
    # Run data extraction test
    extraction_success = run_test("Data Extraction Test", "test_data_extraction.py")
    
    # Run API test (requires server to be running)
    logger.info("Starting server for API test...")
    server_process = subprocess.Popen(["py", "run_server.py"])
    
    # Wait for server to start
    logger.info("Waiting for server to start...")
    time.sleep(5)
    
    # Run API test
    api_success = run_test("API Test", "test_api.py")
    
    # Terminate server
    logger.info("Terminating server...")
    server_process.terminate()
    
    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"Network Model Test: {'PASSED' if network_success else 'FAILED'}")
    logger.info(f"Data Extraction Test: {'PASSED' if extraction_success else 'FAILED'}")
    logger.info(f"API Test: {'PASSED' if api_success else 'FAILED'}")
    
    # Return overall success
    overall_success = network_success and extraction_success and api_success
    if overall_success:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 