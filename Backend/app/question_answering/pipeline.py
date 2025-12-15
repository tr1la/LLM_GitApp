import openai  # Added import for OpenAI
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


# Cấu hình

def ask_general_question(question: str) -> str:
    system_prompt = (
        "You are an intelligent assistant designed to help blind users. "
        "Answer the question clearly, concisely, and in plain language. "
        "Avoid referring to visuals. Speak as if you're reading out loud."
    )

    try:
        
        # Use OpenAI instead of Gemini
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        if not response.choices or not response.choices[0].message.content:
            return "I cannot answer this question due to safety filters."
            
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Google API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get response from Google API: {str(e)}")
