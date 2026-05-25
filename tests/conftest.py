import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    """Create and configure a clean Flask application instance for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "DEBUG": False
    })

    # Setup standard database schemas
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A clean HTTP testing client for the application."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Isolated SQL session for database operations within application context."""
    with app.app_context():
        yield db.session
