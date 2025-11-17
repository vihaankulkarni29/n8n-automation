"""
Configuration management for lead generation system
Simple implementation using .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Simple configuration class"""
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # Google Sheets
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    
    # Scoring thresholds
    MIN_SCORE_THRESHOLD = int(os.getenv('MIN_SCORE_THRESHOLD', '40'))
    
    # Batch processing
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))
    
    # Rate limiting
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2.0'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ['GOOGLE_MAPS_API_KEY', 'GOOGLE_SHEET_ID']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def get(cls, key, default=None):
        """Get config value with optional default"""
        return getattr(cls, key, default)

config = Config()
