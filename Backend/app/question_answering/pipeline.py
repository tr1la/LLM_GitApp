import google.generativeai as genai
import os
from fastapi import HTTPException
from dotenv import load_dotenv # <--- 1. Thêm thư viện này
from ..config import config
# 2. Load file .env ngay lập tức


api_key = config.GOOGLE_API_KEY
# Debug: In ra để kiểm tra xem đã nhận được key chưa (Chỉ in 5 ký tự đầu để bảo mật)
if api_key:
    print(f"✅ Found Google API Key: {api_key[:5]}...")
else:
    print("❌ GOOGLE_API_KEY is missing!")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Cấu hình
genai.configure(api_key = config.GOOGLE_API_KEY)

def ask_general_question(question: str) -> str:
    system_prompt = (
        "You are an intelligent assistant designed to help blind users. "
        "Answer the question clearly, concisely, and in plain language. "
        "Avoid referring to visuals. Speak as if you're reading out loud."
    )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_prompt
        )

        response = model.generate_content(question)
        
        # Kiểm tra nếu bị chặn do safety filter
        if not response.text:
            return "I cannot answer this question due to safety filters."

        return response.text.strip()

    except Exception as e:
        print(f"Google API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get response from Google API: {str(e)}")