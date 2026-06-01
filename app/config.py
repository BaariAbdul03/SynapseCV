import os

class Config:
    """Base Configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-synapse-cv-secret-key-change-in-prod")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # Flask settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit
    
    # Gemini API settings
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_TIMEOUT = float(os.environ.get("GEMINI_TIMEOUT", "20.0"))  # seconds
    GEMINI_RETRIES = int(os.environ.get("GEMINI_RETRIES", "1"))
    
    # Database (Supabase / SQLite)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///synapsecv.db")
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    # Rate Limiting defaults
    RATELIMIT_DEFAULT = "100 per day"
    RATELIMIT_STORAGE_URI = "memory://"
    
    # OAuth configuration (Google)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    ENV = "development"
    # Local dev defaults
    RATELIMIT_ENABLED = False  # Disable rate limit for dev convenience

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    ENV = "production"
    RATELIMIT_ENABLED = True
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = True
    
    # Configure NullPool to prevent connection pooling issues with Supabase transaction pooler
    from sqlalchemy.pool import NullPool
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
    }
    
    # Talisman CSP configurations
    CSP_POLICY = {
        'default-src': '\'self\'',
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com',
            'https://unpkg.com'
        ],
        'style-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'https://fonts.googleapis.com',
            'https://cdnjs.cloudflare.com'
        ],
        'font-src': [
            '\'self\'',
            'https://fonts.gstatic.com'
        ],
        'img-src': [
            '\'self\'',
            'data:',
            'https://images.unsplash.com'
        ],
        'connect-src': [
            '\'self\'',
            'https://cdnjs.cloudflare.com',
            'https://unpkg.com'
        ],
        'worker-src': [
            '\'self\'',
            'blob:'
        ]
    }

class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
