import openai  # Added import for OpenAI
from ast import List
import re
from tempfile import NamedTemporaryFile
import os
import logging
from fpdf import FPDF
import asyncio
from ..config import config
from gtts import gTTS

# --- Mới: Thêm các thư viện cho Google Gemini và xử lý ảnh ---
import base64
import io
from PIL import Image
# -------------------------------------------------------------

# Cấu hình Google API một lần khi import module

def segment_text_by_sentence(text):
    sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
    boundaries_indices = [boundary.start() for boundary in sentence_boundaries]
    
    segments = []
    start = 0
    for boundary_index in boundaries_indices:
        segments.append(text[start:boundary_index + 1].strip())
        start = boundary_index + 1
    segments.append(text[start:].strip())

    return segments

def create_pdf(text: str, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    # Lưu ý: Đảm bảo đường dẫn font là đúng
    try:
        pdf.add_font("FreeSerif", fname="./app/FreeSerif.ttf", uni=True)
        pdf.set_font("FreeSerif", size=12)
    except:
        pdf.set_font("Arial", size=12) # Fallback nếu không tìm thấy font
        
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.multi_cell(0, 10, text)
    pdf.output(output_path)

async def create_pdf_async(text: str, pdf_path: str):
    await asyncio.to_thread(create_pdf, text, pdf_path)

def format_response_distance_estimate_with_openai(response, transcribe, base64_image):
    """
    (Tên hàm giữ nguyên để tránh sửa main.py, nhưng bên trong dùng Google Gemini)
    """
    try:
        if response is None or len(response) == 0:
            return "No objects detected at the moment."
            
        logging.info(f"Processing response with OpenAI: {response}")

        # System Prompt
        system_prompt = """
            You are an expert in guiding visually impaired individuals to move safely and retrieve objects. Your task is to convert object detection data into clear, detailed, and safe movement instructions in English. Include the following:

            - Identify and describe the location of the requested object.
            - Provide clear step-by-step instructions on how to reach the object.
            - Highlight any potential hazards or obstacles and suggest how to avoid them.
            - Use precise directional language (e.g., left, right, forward, backward) and distances.
            - Ensure the instructions are easy to understand and prioritize safety.

            Example format:
            "To reach the [object], follow these steps:
            1. Move forward approximately [distance] inches.
            2. Turn [direction] and continue for [distance] inches.
            3. Watch out for [hazard] located at [location].
            4. The [object] is located at [final position]."
        """

        # Use OpenAI instead of Gemini
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Xử lý ảnh: Decode Base64 thành PIL Image
        try:
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
        except Exception as img_err:
            logging.error(f"Error decoding image: {img_err}")
            return "Error processing the image data."

        # Tạo nội dung prompt (Text + Image)
        user_prompt = f"Object Detection Data: {str(response)}\nUser Transcription/Request: {transcribe}"
        
        # Convert image to base64 for OpenAI
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Gửi request đến OpenAI
        response_openai = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                ]}
            ],
            max_tokens=500
        )

        formatted_response = response_openai.choices[0].message.content.strip()
        
        logging.info(f"Formatted response: {formatted_response}")

        return formatted_response

    except Exception as e:
        logging.error(f"Unexpected error in distance estimation (OpenAI): {e}")
        return str(response)
    
def format_response_product_recognition_with_openai(response):
    """
    (Tên hàm giữ nguyên để tránh sửa main.py, nhưng bên trong dùng Google Gemini)
    """
    try:
        # System Prompt
        system_prompt = """
        Your task is to convert product information into a detailed, easy-to-understand, and engaging paragraph in English.

        Requirements:
        - Provide a full description of the product.
        - Explain nutritional information in a simple way.
        - Evaluate the nutritional value and potential use.
        - Use a friendly, professional tone.

        Example format:
        "[Product Name] by [Brand Name] – A unique culinary experience!

        Product Details:
        - Type: [Detailed description]
        - Weight: [Weight]
        - Category: [Relevant categories]

        Nutritional Value (In-depth analysis):
        [Detailed breakdown of energy, fat, carbohydrates, and protein]"
        """

        # Use OpenAI instead of Gemini
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Gửi request đến OpenAI
        response_openai = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(response)}
            ],
            max_tokens=500
        )

        formatted_description = response_openai.choices[0].message.content.strip()
        
        return formatted_description

    except Exception as e:
        logging.error(f"Unexpected error in product information processing (OpenAI): {e}")
        return str(response)

def format_response_music_detection_with_openai(response):
    pass

def format_response_general_question_answering_with_openai(response):
    pass

def format_audio_response(response, task):
    if task == "distance_estimate":
        full_text = f"The estimated distance to the object is approximately {response} meters."

    elif task == "product_recognition":
        # Xử lý an toàn hơn nếu response không phải dict
        if isinstance(response, dict):
            product_text = f"Product: {response.get('name', 'Unknown')}, Brand: {response.get('brand', 'Unknown')}, Quantity: {response.get('quantity', 'Unknown')}."
            nutrition_data = response.get('nutrition', {})
            if isinstance(nutrition_data, dict):
                nutrition_text = " ".join(
                    [f"{nutrient.replace('_', ' ')}: {amount}" for nutrient, amount in nutrition_data.items()]
                )
            else:
                nutrition_text = "No nutrition info."
            full_text = f"{product_text} Nutrition Information: {nutrition_text}"
        else:
            full_text = str(response)

    elif task == "currency_detection":
         if isinstance(response, dict):
            full_text = f"The total amount detected is {response.get('total_amount', 0)} Vietnamese Dong."
         else:
             full_text = str(response)

    elif task == "text_recognition":
        full_text = f"The text in the image says: {response}"

    elif task == "image_captioning":
        full_text = f"This image can be described as: {response}"

    elif task == "music_recognition":
        if isinstance(response, dict):
            full_text = (
                f"You are listening to '{response.get('title', 'Unknown')}' by {response.get('artist', 'Unknown')}. "
                f"It was released in {response.get('year', 'an unknown year')}."
            )
        else:
            full_text = str(response)

    elif task == "general_question_answering":
        full_text = response

    else:
        full_text = "I'm sorry, I couldn't determine the type of response to generate."

    try:
        # Generate voice output using gTTS
        audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        tts = gTTS(full_text, lang="en")
        tts.save(audio_file.name)

        return audio_file.name
    except Exception as e:
        logging.error(f"Error generating audio response: {e}")
        return None


def format_article_audio_response(response):
    try:
        # Generate voice output using gTTS

        full_text = f"Title: {response.title} \n\n Content: {response.text}"
        audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        tts = gTTS(full_text, lang="en")
        tts.save(audio_file.name)

        full_text = f"Title: {response.title} \n\n Summary: {response.summary}"
        summary_audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        tts = gTTS(full_text, lang="en")
        tts.save(summary_audio_file.name)

        return audio_file.name, summary_audio_file.name
    except Exception as e:
        logging.error(f"Error generating audio response: {e}")
        return None, None