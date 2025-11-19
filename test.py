# test_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# List all available models
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Available: {model.name}")