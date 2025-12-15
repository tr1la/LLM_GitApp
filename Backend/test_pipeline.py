#!/usr/bin/env python3

from app.all_task.pipeline import get_llm_response
import base64

if __name__ == "__main__":
    # Test with a sample image
    image_path = "./examples/image_captioning.png"
    
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Updated:response = get_llm_response("Describe this image", "image_captioning", base64_image, provider="gemini")
        response = get_llm_response("Describe this image", "image_captioning", base64_image, provider="openai")  # Changed from "gemini" to "openai"
        print("Response:", response)
        
    except FileNotFoundError:
        print(f"Image file not found at {image_path}")
        print("Testing without image...")
        # Updated:response = get_llm_response("What is the capital of France?", "general_question_answering", None, provider="gemini")
        response = get_llm_response("What is the capital of France?", "general_question_answering", None, provider="openai")  # Changed from "gemini" to "openai"
        print("Response:", response)