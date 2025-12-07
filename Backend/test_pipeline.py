#!/usr/bin/env python3
"""
Test the full LLM pipeline
"""
import sys
sys.path.insert(0, '/Users/tr1la/Documents/LLMProj/LLM_application/ml_service')

from app.all_task.pipeline import get_llm_response

try:
    print("Testing full LLM pipeline...")
    print("-" * 60)
    
    response = get_llm_response(
        query="What is 2 + 2?",
        task="general_question_answering",
        base64_image=None,
        provider="gemini"
    )
    
    print(f"✅ SUCCESS!")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    import traceback
    traceback.print_exc()
