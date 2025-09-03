import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}\n")

# Configure the Gemini API
genai.configure(api_key=api_key)

# List available models
print("Available models: ")
for m in genai.list_models():
    print(f"- {m}")

# Create a model instance
model = genai.GenerativeModel('models/gemini-2.0-flash')

try:
    # Generate content
    response = model.generate_content("Say hello!")
    print("\nResponse:", response.text)
except Exception as e:
    print("\nError occurred:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}") 