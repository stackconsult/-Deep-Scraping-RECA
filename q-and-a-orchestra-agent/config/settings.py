from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ValidationInfo
from typing import Optional, List
import os
from pathlib import Path

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
    # Make optional with default for local dev ease, or enforce strictness in production
    DATABASE_URL: str = Field("postgresql://orchestra:password@localhost:5432/orchestra_db", description="PostgreSQL Database URL")
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis URL")
    
    # LLM & AI - API Keys
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
    
    @field_validator("GOOGLE_API_KEY")
    @classmethod
    def validate_core_llm_key(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        # Validation logic
        if not v and info.data.get("ENVIRONMENT") == "production":
            # Just log warning in practice, don't crash unless strictly required
            pass 
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )

# Global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"❌ Configuration Validation Error: {e}")
    # Fallback for development if .env is missing/invalid
    settings = None

