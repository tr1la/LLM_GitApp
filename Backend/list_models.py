#!/usr/bin/env python3
"""
Check available Gemini models
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file")
    exit(1)

try:
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    
    print("📋 Available Gemini Models:")
    print("-" * 60)
    
    models = genai.list_models()
    for model in models:
        print(f"Name: {model.name}")
        if hasattr(model, 'description'):
            print(f"Description: {model.description}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"Methods: {model.supported_generation_methods}")
        print()
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    import traceback
    traceback.print_exc()
