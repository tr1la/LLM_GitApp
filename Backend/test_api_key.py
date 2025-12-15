#!/usr/bin/env python3
"""
Test script to validate the Google Gemini API key
"""
import os
import openai  # Added import for OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")  # Changed from GOOGLE_API_KEY to OPENAI_API_KEY

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env file")  # Changed message
    exit(1)

print(f"Testing API Key: {api_key[:20]}...")
print(f"Full key length: {len(api_key)}")

# Try using the openai library instead of google-generativeai
try:
    print("\n[1] Configuring OpenAI API...")  # Changed message
    client = openai.OpenAI(api_key=api_key)  # Changed to OpenAI client
    
    print("[2] Creating model instance...")
    # OpenAI doesn't need explicit model instantiation like Gemini
    
    print("[3] Sending test request...")
    response = client.chat.completions.create(  # Changed to OpenAI chat completions
        model="gpt-4o-mini",  # Specify the model
        messages=[{"role": "user", "content": "Say 'API key is valid' in one sentence"}],
        max_tokens=50
    )
    
    print(f"✅ SUCCESS! Response: {response.choices[0].message.content[:100]}")  # Changed to access OpenAI response
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    
    # Try to get more details
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()