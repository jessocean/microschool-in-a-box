# Weight Management System - Backend

This is the backend for the Weight Management System, which implements an obesity factor network model using NetworkX.

## Features

- Bayesian updates for network parameters
- Intervention potential calculations
- Recommendation generation
- Network visualization
- RESTful API endpoints

## Setup

1. Create a virtual environment:
```bash
py -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the FastAPI server:
```bash
py main.py
```

The server will be available at http://localhost:8000.

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `GET /`: Root endpoint
- `GET /factors`: Get all factors and their current values
- `POST /factors/{factor}`: Update a factor's value
- `GET /relationships`: Get all relationships in the network
- `POST /relationships`: Update a relationship's strength
- `GET /recommendations`: Get top n recommendations based on intervention potential
- `GET /network-state`: Get the current state of the network
- `POST /network-state`: Set the network state
- `GET /visualization`: Get a visualization of the network

## Network Model

The obesity factor network model is implemented in `simplified_obesity_network.py`. It includes:

- 10 key factors affecting weight management
- Bayesian updates for factor values and relationship strengths
- Intervention potential calculations
- Recommendation generation based on highest impact factors

## Example Usage

```python
from simplified_obesity_network import SimpleObesityNetwork

# Create the network
network = SimpleObesityNetwork()

# Get top recommendations
recommendations = network.get_top_recommendations(3)
print("Top recommendations:")
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec['factor']} - {rec['description']} - {rec['direction']} (impact: {rec['potential']:.2f})")

# Update based on user data
network.update_factor("sleep_quality", 0.3)  # User has poor sleep
network.update_factor("stress_level", 0.8)  # User has high stress

# Get updated recommendations
updated_recommendations = network.get_top_recommendations(3)
``` 