from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # General
    DOMAIN: str = "http://localhost:8000"
    
    # Database Configuration
    MONGO_URI: str = "mongodb://admin:password@localhost:27017"
    DATABASE_NAME: str = "cims"
    
    # Token Configuration
    SECRET_KEY: str  = "your_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"
    
    # Email Configuration
    SMTP_SERVER: str = "mail.cims.homes"
    SMTP_PORT: int = 465
    SMTP_SENDER_EMAIL: str = "noreply@cims.homes"
    SMTP_SENDER_PASSWORD: str = "Zxv14DDDTX"
    
    class Config:
        env_file = ".env"

settings = Settings()
