import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Railway Configuration
    RAILWAY_HOST: str = os.getenv("RAILWAY_HOST", "iploppositionplanningbackend-game-planner.up.railway.app")
    RAILWAY_PORT: int = int(os.getenv("RAILWAY_PORT", "8000"))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Local React development
        "http://127.0.0.1:3000",  # Alternative local address
        "https://iploppositionplanningbackend-game-planner.up.railway.app",  # Railway backend
        "*"  # Allow all origins for now (can be restricted later)
    ]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def api_url(self) -> str:
        """Get the appropriate API URL based on environment"""
        if self.is_production:
            return f"https://{self.RAILWAY_HOST}"
        else:
            return f"http://{self.HOST}:{self.PORT}"

# Create settings instance
settings = Settings()
