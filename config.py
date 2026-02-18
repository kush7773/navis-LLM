import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'navis-secret-key-2024')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    TRAINING_DATA_FILE = os.path.join(os.path.dirname(__file__), 'training_data.json')
    SIMILARITY_THRESHOLD = 0.55
