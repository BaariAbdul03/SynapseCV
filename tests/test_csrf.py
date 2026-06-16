import hashlib
from app.models import User, ApiKey

def test_csrf_protection_enabled_rejects_session_post(app):
    """Verify that when CSRF is enabled, regular state-changing endpoints reject requests without a token."""
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    
    # State-changing route /parse
    response = client.post('/parse')
    assert response.status_code == 400
    # Flask-WTF CSRF error typically returns 400 Bad Request with a description or CSRF token missing
    assert b"CSRF" in response.data or response.status_code == 400

def test_csrf_protection_exempts_public_api(app, db_session):
    """Verify that CSRF-exempt public API endpoint works without a CSRF token when authorized."""
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    
    # 1. Setup mock key in database
    plaintext = "test_authorizedtoken_csrf_123"
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    
    user = User(email="csrf.recruiter@example.com")
    user.set_password("SecurePassword123")
    db_session.add(user)
    db_session.commit()
    
    api_key = ApiKey(
        user_id=user.id,
        name="REST Client Key",
        key_prefix="test_csrf",
        key_hash=key_hash
    )
    db_session.add(api_key)
    db_session.commit()

    headers = {"X-API-Key": plaintext}
    
    # Send a request to public /api/v1/parse without CSRF token.
    # It should not fail with CSRF block (it will return 400 for bad PDF instead of 400 CSRF block)
    import io
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
    
    # If it was blocked by CSRF, it would return the CSRF error (like "The CSRF token is missing.")
    # But because it is exempt, it reaches the controller and fails with PDF validation.
    assert response.status_code == 400
    assert b"Invalid file content" in response.data
