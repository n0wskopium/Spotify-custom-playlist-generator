import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file.")
else:
    try:
        genai.configure(api_key=api_key)
        print(f"✅ Authenticated with API Key: {api_key[:5]}...{api_key[-5:]}")
        print("\n📋 Available Models for Content Generation:")
        
        found_any = False
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  • {model.name}")
                found_any = True
        
        if not found_any:
            print("⚠️ No models found that support 'generateContent'. Check your API key permissions.")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")