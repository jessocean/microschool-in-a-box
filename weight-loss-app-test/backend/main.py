from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import os
import logging
from simplified_obesity_network import SimpleObesityNetwork
from data_extraction import ConversationDataExtractor
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("weight-management-api")

app = FastAPI(title="Weight Management API", description="API for the weight management system")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the network model
network = SimpleObesityNetwork()

# Initialize the data extractor
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    logger.warning("ANTHROPIC_API_KEY environment variable not set. Data extraction will not work.")
    data_extractor = None
else:
    data_extractor = ConversationDataExtractor(api_key)

# Pydantic models for request/response validation
class FactorUpdate(BaseModel):
    factor: str
    value: float
    confidence: Optional[float] = 0.7

class RelationshipUpdate(BaseModel):
    source: str
    target: str
    strength: float
    confidence: Optional[float] = 0.7

class NetworkState(BaseModel):
    factors: Dict[str, float]
    relationships: List[Dict[str, Any]]

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]

class ConversationRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class ConversationResponse(BaseModel):
    response: str
    recommendations: List[Dict[str, Any]]
    extracted_data: Optional[Dict[str, Any]] = None

# API endpoints
@app.get("/")
async def root():
    return {"message": "Weight Management API"}

@app.get("/factors", response_model=Dict[str, Dict[str, Any]])
async def get_factors():
    """Get all factors and their current values"""
    return network.factors

@app.post("/factors/{factor}")
async def update_factor(factor: str, update: FactorUpdate):
    """Update a factor's value"""
    success = network.update_factor(factor, update.value, update.confidence)
    if not success:
        raise HTTPException(status_code=400, detail=f"Invalid factor: {factor}")
    return {"message": f"Factor {factor} updated successfully"}

@app.get("/relationships")
async def get_relationships():
    """Get all relationships in the network"""
    relationships = []
    for source, target, data in network.G.edges(data=True):
        relationships.append({
            "from": source,
            "to": target,
            "weight": data["weight"],
            "confidence": data["confidence"]
        })
    return relationships

@app.post("/relationships")
async def update_relationship(update: RelationshipUpdate):
    """Update a relationship's strength"""
    success = network.update_relationship(
        update.source, update.target, update.strength, update.confidence
    )
    if not success:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid relationship: {update.source} -> {update.target}"
        )
    return {"message": "Relationship updated successfully"}

@app.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(n: int = 3):
    """Get top n recommendations based on intervention potential"""
    recommendations = network.get_top_recommendations(n)
    return {"recommendations": recommendations}

@app.get("/network-state", response_model=NetworkState)
async def get_network_state():
    """Get the current state of the network"""
    return network.get_network_state()

@app.post("/network-state")
async def set_network_state(state: NetworkState):
    """Set the network state"""
    success = network.set_network_state(state.dict())
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set network state")
    return {"message": "Network state updated successfully"}

@app.get("/visualization")
async def get_visualization():
    """Get a visualization of the network"""
    fig = network.visualize_network()
    # In a real implementation, you would save this to a file or return as base64
    # For now, we'll just return a success message
    return {"message": "Visualization generated successfully"}

@app.post("/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest):
    """
    Process a chat message, extract data, update the network, and return recommendations
    """
    # Get recommendations from the network model
    recommendations = network.get_top_recommendations(3)
    
    # Extract data from the conversation if data extractor is available
    extracted_data = None
    if data_extractor and request.conversation_history:
        # Combine conversation history into a single string
        conversation = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in request.conversation_history
        ])
        conversation += f"\nuser: {request.message}"
        
        # Extract data
        extracted_data = data_extractor.extract_data(conversation)
        
        # Update network with extracted data
        data_extractor.update_network(extracted_data)
        
        # Get updated recommendations
        recommendations = network.get_top_recommendations(3)
    
    # Format recommendations for Claude
    recommendations_text = "\n".join([
        f"- {rec['factor']}: {rec['direction']} (impact: {rec['potential']:.2f})"
        for rec in recommendations
    ])
    
    # Create the prompt for Claude
    prompt = f"""You are a weight management coach. Use the following recommendations from our network model to inform your response, but maintain a natural, conversational tone:

{recommendations_text}

User message: {request.message}

Respond in a helpful, empathetic way while incorporating relevant recommendations when appropriate."""
    
    # Get response from Claude
    from anthropic import Anthropic
    anthropic = Anthropic(api_key=api_key)
    
    completion = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = completion.content[0].text
    
    return {
        "response": response_text,
        "recommendations": recommendations,
        "extracted_data": extracted_data
    }

# Run the server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 