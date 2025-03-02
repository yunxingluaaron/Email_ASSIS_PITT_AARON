import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base config."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True

class TestingConfig(Config):
    """Testing config."""
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    """Production config."""
    DEBUG = False

# Config dictionary to easily select the desired configuration
config_by_name = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig
}