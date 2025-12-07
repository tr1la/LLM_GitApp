import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config(object):

    def __init__(self):
        self.HOST = os.getenv('HOST')
        self.PORT = os.getenv('PORT')
        self.MONGODB_URI = os.getenv('MONGODB_URI')
        self.DB_NAME = os.getenv('DB_NAME')
        self.DB_COLLECTION = os.getenv('DB_COLLECTION')
        self.DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        # self.VOICE_RSS = os.getenv('Voice_RSS')
        
        # Validate critical API keys
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is not set. Please check your .env file.")

config = Config()
