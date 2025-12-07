#!/usr/bin/env python3
"""
Test the general_question_answering endpoint
"""
import sys
sys.path.insert(0, '/Users/tr1la/Documents/LLMProj/LLM_application/ml_service')

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Testing /general_question_answering endpoint...")
print("-" * 60)

try:
    response = client.post(
        "/general_question_answering",
        data={"message": "What is 2 + 2?"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Endpoint working!")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
