import os
import logging
from data_extraction import ConversationDataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("data-extraction-test")

def test_data_extraction():
    """Test the data extraction functionality"""
    logger.info("Testing data extraction...")
    
    # Load API key from environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return False
    
    # Create the extractor
    extractor = ConversationDataExtractor(api_key)
    
    # Test conversations
    conversations = [
        """
        I've been having trouble sleeping lately, maybe 5 hours a night. 
        I'm also feeling very stressed at work, which is making me eat more. 
        I try to exercise but only manage to do it once a week.
        """,
        """
        I've been trying to eat healthier and have cut down on calories.
        I'm also walking for 30 minutes every day, which has helped with my stress levels.
        I'm still having trouble with sleep though, only getting about 6 hours a night.
        """,
        """
        I've been feeling really good lately! I'm sleeping 8 hours a night,
        eating a balanced diet, and exercising 4 times a week. My stress levels
        are down, and I've lost some weight.
        """
    ]
    
    # Process each conversation
    for i, conversation in enumerate(conversations, 1):
        logger.info(f"Processing conversation {i}...")
        
        # Extract data
        extracted_data = extractor.extract_data(conversation)
        logger.info(f"Extracted data: {extracted_data}")
        
        # Update network
        extractor.update_network(extracted_data)
        
        # Get recommendations
        recommendations = extractor.get_recommendations(3)
        logger.info(f"Recommendations after conversation {i}:")
        for j, rec in enumerate(recommendations, 1):
            logger.info(f"{j}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")
        
        logger.info("")
    
    logger.info("Data extraction test completed successfully!")
    return True

if __name__ == "__main__":
    test_data_extraction() 