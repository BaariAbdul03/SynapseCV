import pytest
import os
from app.config import validate_production_config

def test_validate_production_config_valid():
    """Verify that a valid configuration passes validation."""
    config = {
        "SECRET_KEY": "a-secure-production-only-key",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
        "GROQ_API_KEY": "gsk_123",
        "GEMINI_API_KEY": "gemini_456"
    }
    
    # Mock environment variables
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    
    try:
        validate_production_config(config)
    except ValueError as e:
        pytest.fail(f"validate_production_config failed unexpectedly: {e}")

def test_validate_production_config_invalid_secret_key():
    """Verify that default or empty SECRET_KEY raises ValueError in production."""
    # Default SECRET_KEY
    config1 = {
        "SECRET_KEY": "default-synapse-cv-secret-key-change-in-prod",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
        "GROQ_API_KEY": "gsk_123"
    }
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    with pytest.raises(ValueError, match="SECRET_KEY must be set to a secure, custom value"):
        validate_production_config(config1)

    # Empty SECRET_KEY
    config2 = {
        "SECRET_KEY": "",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
        "GROQ_API_KEY": "gsk_123"
    }
    with pytest.raises(ValueError, match="SECRET_KEY must be set to a secure, custom value"):
        validate_production_config(config2)

def test_validate_production_config_invalid_database():
    """Verify that SQLite or missing DATABASE_URL raises ValueError in production."""
    # SQLite DB
    config1 = {
        "SECRET_KEY": "secure-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///synapsecv.db",
        "GROQ_API_KEY": "gsk_123"
    }
    os.environ["DATABASE_URL"] = "sqlite:///synapsecv.db"
    with pytest.raises(ValueError, match="DATABASE_URL must be configured with a production database"):
        validate_production_config(config1)

    # Missing DATABASE_URL env var
    config2 = {
        "SECRET_KEY": "secure-key",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
        "GROQ_API_KEY": "gsk_123"
    }
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    with pytest.raises(ValueError, match="DATABASE_URL must be configured with a production database"):
        validate_production_config(config2)

def test_validate_production_config_oauth_required():
    """Verify that OAuth keys are validated when OAUTH_REQUIRED is true."""
    config = {
        "SECRET_KEY": "secure-key",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
        "GROQ_API_KEY": "gsk_123",
        "GOOGLE_CLIENT_ID": "",
        "GOOGLE_CLIENT_SECRET": ""
    }
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    os.environ["OAUTH_REQUIRED"] = "true"
    
    with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured"):
        validate_production_config(config)
        
    # Set them
    config["GOOGLE_CLIENT_ID"] = "client-id"
    config["GOOGLE_CLIENT_SECRET"] = "client-secret"
    validate_production_config(config)
    
    # Reset env var
    os.environ["OAUTH_REQUIRED"] = "false"

def test_validate_production_config_missing_ai_keys():
    """Verify that missing both GROQ and GEMINI API keys raises ValueError in production."""
    config = {
        "SECRET_KEY": "secure-key",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@localhost/db",
        "GROQ_API_KEY": "",
        "GEMINI_API_KEY": ""
    }
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    with pytest.raises(ValueError, match="At least one AI provider API key"):
        validate_production_config(config)
