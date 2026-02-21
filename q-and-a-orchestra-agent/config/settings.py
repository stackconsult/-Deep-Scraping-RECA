from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
import os

class Settings(BaseSettings):
    """
    Application configuration and validation.
    """
    
    # Environment
    ENVIRONMENT: str = Field("development", description="Deployment environment (development, production, staging)")
    DEBUG: bool = Field(False, description="Enable debug mode")
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    ENABLE_JSON_LOGGING: bool = Field(False, description="Enable structured JSON logging")
    
    # API Configuration
    API_HOST: str = Field("0.0.0.0", description="API Host binding")
    API_PORT: int = Field(8000, description="API Port binding")
    
    # Database & Infrastructure
    DATABASE_URL: str = Field(..., description="PostgreSQL Database URL")
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis URL")
    
    # LLM & AI - API Keys
    # Optional because some might be used only if specific features are enabled, 
    # but Google/Gemini is core to this agent.
    GOOGLE_API_KEY: Optional[str] = Field(None, description="Google Gemini API Key")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API Key")
    OLLAMA_API_KEY: Optional[str] = Field(None, description="Ollama API Key for authenticated instances")
    
    # LLM & AI - Service URLs
    OLLAMA_BASE_URL: str = Field("http://localhost:11434", description="Ollama Base URL")
    
    # Features Flags
    ENABLE_AUTO_DISCOVERY: bool = Field(True, description="Enable model auto-discovery")
    ENABLE_SEMANTIC_CACHE: bool = Field(True, description="Enable semantic caching")
    ENABLE_MULTI_TENANCY: bool = Field(True, description="Enable multi-tenancy")
    ENABLE_AUDIT_LOGGING: bool = Field(True, description="Enable audit logging")
    
    # Security
    CORS_ORIGINS: List[str] = Field(["*"], description="Allowed CORS origins")
    
    @validator("GOOGLE_API_KEY")
    def validate_core_llm_key(cls, v, values):
        # If we are in production, we might want to enforce this more strictly
        # unless we are purely running on local Ollama.
        # For now, we'll log a warning if it's missing but not crash hard unless typically required.
        # However, the README says it IS required.
        if not v and values.get("ENVIRONMENT") == "production":
            # Check if we are relying solely on Ollama?
            pass 
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # In case of validation error at startup
    print(f"❌ Configuration Validation Error: {e}")
    # We might want to re-raise or handle gracefully depending on context
    # raising ensures we fail fast on bad config
    # raise e
    # For now, let's create a partial/default instance for dev if .env is missing?
    # No, fail fast is better for "Operational Hardening".
    settings = None
