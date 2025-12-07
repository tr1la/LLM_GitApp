"""
NLTK data initialization script
Downloads required NLTK data on first run
"""
import nltk
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def download_nltk_data():
    """Download required NLTK data for article processing"""
    try:
        # Try to use punkt_tab first (newer version)
        try:
            nltk.data.find('tokenizers/punkt_tab')
            logger.info("✅ NLTK punkt_tab already available")
        except LookupError:
            logger.info("📥 Downloading NLTK punkt_tab...")
            nltk.download('punkt_tab', quiet=True)
            logger.info("✅ NLTK punkt_tab downloaded")
    except Exception as e:
        logger.warning(f"⚠️ Failed to download punkt_tab: {e}")
        try:
            logger.info("Attempting fallback to punkt...")
            nltk.download('punkt', quiet=True)
            logger.info("✅ NLTK punkt downloaded as fallback")
        except Exception as e2:
            logger.error(f"❌ Failed to download NLTK data: {e2}")

if __name__ == "__main__":
    download_nltk_data()

