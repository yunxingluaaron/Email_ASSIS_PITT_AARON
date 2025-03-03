import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base config."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'email_analyzer')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True

class TestingConfig(Config):
    """Testing config."""
    DEBUG = True
    TESTING = True
    # Use a different database for testing
    DB_NAME = os.getenv('DB_NAME_TEST', 'email_analyzer_test')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"

class ProductionConfig(Config):
    """Production config."""
    DEBUG = False
    # Use environment variables strictly in production
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)

# Config dictionary to easily select the desired configuration
config_by_name = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig
}