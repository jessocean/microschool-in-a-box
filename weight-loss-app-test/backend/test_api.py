import requests
import json
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("api-test")

# API base URL
BASE_URL = "http://localhost:8000"

def test_api():
    """Test the Weight Management API"""
    logger.info("Testing Weight Management API...")
    
    # Test root endpoint
    logger.info("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    logger.info(f"Root endpoint response: {response.json()}")
    
    # Test getting factors
    logger.info("Testing getting factors...")
    response = requests.get(f"{BASE_URL}/factors")
    assert response.status_code == 200
    factors = response.json()
    logger.info(f"Factors: {json.dumps(factors, indent=2)}")
    
    # Test getting relationships
    logger.info("Testing getting relationships...")
    response = requests.get(f"{BASE_URL}/relationships")
    assert response.status_code == 200
    relationships = response.json()
    logger.info(f"Relationships: {json.dumps(relationships, indent=2)}")
    
    # Test getting recommendations
    logger.info("Testing getting recommendations...")
    response = requests.get(f"{BASE_URL}/recommendations")
    assert response.status_code == 200
    recommendations = response.json()
    logger.info(f"Recommendations: {json.dumps(recommendations, indent=2)}")
    
    # Test updating a factor
    logger.info("Testing updating a factor...")
    factor = "sleep_quality"
    value = 0.3
    response = requests.post(
        f"{BASE_URL}/factors/{factor}",
        json={"factor": factor, "value": value, "confidence": 0.8}
    )
    assert response.status_code == 200
    logger.info(f"Update factor response: {response.json()}")
    
    # Test getting updated recommendations
    logger.info("Testing getting updated recommendations...")
    response = requests.get(f"{BASE_URL}/recommendations")
    assert response.status_code == 200
    updated_recommendations = response.json()
    logger.info(f"Updated recommendations: {json.dumps(updated_recommendations, indent=2)}")
    
    # Test chat endpoint
    logger.info("Testing chat endpoint...")
    message = "I've been having trouble sleeping lately, maybe 5 hours a night. I'm also feeling very stressed at work."
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message}
    )
    assert response.status_code == 200
    chat_response = response.json()
    logger.info(f"Chat response: {json.dumps(chat_response, indent=2)}")
    
    logger.info("All tests passed successfully!")

if __name__ == "__main__":
    # Wait for the server to start
    logger.info("Waiting for server to start...")
    time.sleep(2)
    
    try:
        test_api()
    except Exception as e:
        logger.error(f"Error testing API: {e}")
        exit(1) 