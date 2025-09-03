# Weight Management System

A comprehensive weight management system that uses a Bayesian network model to analyze factors affecting weight and provide personalized recommendations.

## Features

- Bayesian network model for weight management
- Factor analysis and relationship mapping
- Personalized recommendations based on user data
- Conversation data extraction and processing
- RESTful API endpoints for system interaction
- Claude AI integration for natural language processing

## Project Structure

```
backend/
├── main.py                  # FastAPI application
├── simplified_obesity_network.py  # Network model implementation
├── data_extraction.py       # Conversation data extraction
├── test_api.py             # API testing script
├── test_data_extraction.py # Data extraction testing
├── test_network.py         # Network model testing
├── run_and_test.py         # Development server and test runner
├── run_all_tests.py        # Comprehensive test suite
├── run_production.py       # Production server runner
└── requirements.txt        # Project dependencies
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Set up environment variables:
   ```bash
   # Windows PowerShell
   $env:ANTHROPIC_API_KEY="your-api-key"
   $env:PORT=8000  # Optional, defaults to 8000
   ```

## Running the Application

### Development Mode

```bash
# Run server and tests
py backend/run_and_test.py

# Run all tests
py backend/run_all_tests.py
```

### Production Mode

```bash
py backend/run_production.py
```

## API Endpoints

- `GET /`: Root endpoint
- `GET /factors`: List all factors in the network
- `GET /relationships`: List all relationships in the network
- `GET /recommendations`: Get current recommendations
- `POST /update/{factor}`: Update a factor's value
- `POST /chat`: Process chat messages and get recommendations

## Testing

The project includes several test scripts:

- `test_network.py`: Tests the network model functionality
- `test_data_extraction.py`: Tests conversation data extraction
- `test_api.py`: Tests API endpoints
- `run_all_tests.py`: Runs all tests in sequence

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 