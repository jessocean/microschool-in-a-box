import json
import logging
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from simplified_obesity_network import SimpleObesityNetwork

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("data-extraction")

class ConversationDataExtractor:
    """
    Extract structured data from conversations using Claude's function calling
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the data extractor
        
        Args:
            api_key: Anthropic API key
        """
        self.anthropic = Anthropic(api_key=api_key)
        self.network = SimpleObesityNetwork()
        
        # Define the function schema for Claude
        self.function_schema = {
            "name": "extract_factors",
            "description": "Extract factors and their values from a conversation",
            "parameters": {
                "type": "object",
                "properties": {
                    "factors": {
                        "type": "object",
                        "description": "Map of factor names to their values (0-1 scale)",
                        "additionalProperties": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence in the extracted data (0-1 scale)",
                        "minimum": 0,
                        "maximum": 1
                    }
                },
                "required": ["factors", "confidence"]
            }
        }
    
    def extract_data(self, conversation: str) -> Dict[str, Any]:
        """
        Extract structured data from a conversation
        
        Args:
            conversation: The conversation text
            
        Returns:
            Dict containing extracted factors and confidence
        """
        try:
            # Create the prompt for Claude
            prompt = f"""
            Extract any mentioned factors and their values from this conversation. 
            For each factor, estimate its value on a scale of 0-1, where:
            - 0 represents the worst possible state
            - 1 represents the best possible state
            
            For stress_level, remember that lower values are better.
            
            Conversation:
            {conversation}
            
            Return the data in the format specified by the function schema.
            """
            
            # Call Claude with function calling
            response = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
                tools=[{"type": "function", "function": self.function_schema}]
            )
            
            # Extract the function call result
            tool_calls = response.content[0].tool_calls
            if not tool_calls:
                logger.warning("No function calls returned from Claude")
                return {"factors": {}, "confidence": 0.5}
            
            # Parse the function call arguments
            function_call = tool_calls[0]
            if function_call.function.name != "extract_factors":
                logger.warning(f"Unexpected function name: {function_call.function.name}")
                return {"factors": {}, "confidence": 0.5}
            
            # Parse the arguments
            args = json.loads(function_call.function.arguments)
            logger.info(f"Extracted data: {args}")
            
            return args
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return {"factors": {}, "confidence": 0.5}
    
    def update_network(self, extracted_data: Dict[str, Any]) -> bool:
        """
        Update the network model with extracted data
        
        Args:
            extracted_data: Dict containing extracted factors and confidence
            
        Returns:
            bool: True if update was successful
        """
        try:
            factors = extracted_data.get("factors", {})
            confidence = extracted_data.get("confidence", 0.7)
            
            # Update each factor
            for factor, value in factors.items():
                if factor in self.network.factors:
                    self.network.update_factor(factor, value, confidence)
                    logger.info(f"Updated factor {factor} with value {value} and confidence {confidence}")
                else:
                    logger.warning(f"Unknown factor: {factor}")
            
            return True
        except Exception as e:
            logger.error(f"Error updating network: {e}")
            return False
    
    def get_recommendations(self, n: int = 3) -> List[Dict[str, Any]]:
        """
        Get recommendations from the network model
        
        Args:
            n: Number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        return self.network.get_top_recommendations(n)

# Example usage
if __name__ == "__main__":
    # Load API key from environment variable
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        exit(1)
    
    # Create the extractor
    extractor = ConversationDataExtractor(api_key)
    
    # Example conversation
    conversation = """
    I've been having trouble sleeping lately, maybe 5 hours a night. 
    I'm also feeling very stressed at work, which is making me eat more. 
    I try to exercise but only manage to do it once a week.
    """
    
    # Extract data
    extracted_data = extractor.extract_data(conversation)
    print(f"Extracted data: {extracted_data}")
    
    # Update network
    extractor.update_network(extracted_data)
    
    # Get recommendations
    recommendations = extractor.get_recommendations(3)
    print("\nRecommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})") 