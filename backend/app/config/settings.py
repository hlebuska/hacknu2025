"""
Configuration settings for HackNU25 Backend
"""

import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hacknu25_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Settings:
    """Application settings and configuration"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        logger.info("🔧 Environment variables loaded")
        
        # OpenAI configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.info(f"🔑 OpenAI API key {'configured' if self.openai_api_key else 'missing'}")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        logger.info(f"🤖 OpenAI client {'initialized' if self.openai_client else 'not available'}")
        
        # App configuration
        self.app_title = "HackNU25 Backend API"
        self.app_description = "PDF analysis with OpenAI GPT and text extraction"
        self.app_version = "2.0.0"
        
        # Server configuration
        self.host = "127.0.0.1"
        self.port = 8001
        self.reload = False
        
        # Model configuration
        self.openai_model = "gpt-3.5-turbo"
        self.max_tokens = 2000
        self.temperature = 0.3


# Global settings instance
settings = Settings()