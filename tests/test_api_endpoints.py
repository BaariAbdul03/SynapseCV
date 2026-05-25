import io
import hashlib
from app.models import User, ApiKey

def test_api_unauthorized(client):
    """Verify endpoint rejects requests without credentials."""
    response = client.post('/api/v1/parse')
    assert response.status_code == 401
    assert "Unauthorized" in response.get_json()["error"]

def test_api_invalid_key(client):
    """Verify endpoint rejects invalid credentials."""
    headers = {"Authorization": "Bearer test_invalidtoken"}
    response = client.post('/api/v1/parse', headers=headers)
    assert response.status_code == 401
    assert "invalid or revoked" in response.get_json()["error"]

def test_api_authorized_spoofed_pdf(client, db_session):
    """Verify authorized key with invalid file payload returns validation failure."""
    # 1. Setup mock key in database
    plaintext = "test_authorizedtoken12345"
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    
    user = User(email="api.recruiter@example.com")
    user.set_password("SecurePassword123")
    db_session.add(user)
    db_session.commit()
    
    api_key = ApiKey(
        user_id=user.id,
        name="REST Client Key",
        key_prefix="test_auth",
        key_hash=key_hash
    )
    db_session.add(api_key)
    db_session.commit()

    # 2. Test request with the generated key
    headers = {"X-API-Key": plaintext}
    bad_pdf = io.BytesIO(b"Not a valid PDF signature")
    data = {
        "resume": (bad_pdf, "spoofed.pdf"),
        "job_description": "Architect Developer"
    }
    
    response = client.post(
        '/api/v1/parse',
        headers=headers,
        data=data,
        content_type='multipart/form-data'
    )
    # Rejects as invalid PDF MIME structure
    assert response.status_code == 400
    assert "Invalid file content" in response.get_json()["error"]

def test_swagger_docs_endpoint(client):
    """Verify OpenAPI swagger interface displays correctly."""
    response = client.get('/api/docs/')
    assert response.status_code == 200
    assert b"Swagger" in response.data or b"OpenAPI" in response.data
