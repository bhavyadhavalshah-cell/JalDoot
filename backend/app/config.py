import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings:
    PROJECT_NAME: str = "JalDoot — Machhuaare Ka Saathi, Samundar Ka Saarthi"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/jaldoot"
    )
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR / 'jaldoot.db'}"
    
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jaldoot_super_secret_jwt_key_2026_marine_safety_token")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Hardcoded Admin credentials
    ADMIN_EMAIL: str = "admin@gmail.com"
    ADMIN_PASSWORD: str = "admin1234"
    
    # Gemini AI
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    
    # Free Carrier Email-to-SMS Gateway settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    ADMIN_ALERT_PHONE: str = os.getenv("ADMIN_ALERT_PHONE", "+919876543210")
    ADMIN_CARRIER_GATEWAY: str = os.getenv("ADMIN_CARRIER_GATEWAY", "vtext.com")
    
    # Uploads
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    STATIC_DIR: Path = BASE_DIR.parent / "frontend"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
