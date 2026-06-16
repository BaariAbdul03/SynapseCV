from app.models import User, Analysis

def test_archive_unauthenticated_access_denied(client):
    """Verify that unauthenticated requests to archives are rejected with 401."""
    # 1. Access listing
    response = client.get('/archives')
    assert response.status_code == 401

    # 2. Access specific archive
    response = client.get('/archives/1')
    assert response.status_code == 401

    # 3. Delete specific archive
    response = client.delete('/archives/1')
    assert response.status_code == 401

def test_archive_owner_access(client, db_session):
    """Verify that a logged-in user can access their own archives."""
    # 1. Create owner user
    owner = User(email="owner@example.com", name="Owner Recruiter")
    owner.set_password("OwnerPassword123")
    db_session.add(owner)
    db_session.commit()

    # 2. Log in owner
    login_resp = client.post('/auth/login', data={
        "email": "owner@example.com",
        "password": "OwnerPassword123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200

    # 3. Create analysis archive record
    analysis = Analysis(
        user_id=owner.id,
        candidate_name="John Doe CV",
        detected_role="Software Engineer",
        match_percentage=85,
        skills=["Python", "Flask"],
        education=["B.S. CS"],
        email="john@example.com",
        phone="555-1234",
        github_url="https://github.com/john",
        linkedin_url="https://linkedin.com/in/john",
        missing_keywords=["Docker"],
        profile_summary="Good candidate",
        scoring_reasoning="Started at 100..."
    )
    db_session.add(analysis)
    db_session.commit()

    # 4. Fetch the analysis record
    resp = client.get(f'/archives/{analysis.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "John Doe CV"

    # 5. Fetch all archives
    list_resp = client.get('/archives')
    assert list_resp.status_code == 200
    list_data = list_resp.get_json()
    assert len(list_data) == 1
    assert list_data[0]["id"] == analysis.id

def test_archive_forbidden_access(client, db_session):
    """Verify that a user cannot retrieve or delete another user's archive."""
    # 1. Create owner and malicious users
    owner = User(email="owner2@example.com", name="Owner")
    owner.set_password("password123")
    
    attacker = User(email="attacker@example.com", name="Attacker")
    attacker.set_password("password123")
    
    db_session.add(owner)
    db_session.add(attacker)
    db_session.commit()

    # 2. Create analysis owned by owner
    analysis = Analysis(
        user_id=owner.id,
        candidate_name="Target CV",
        detected_role="Product Manager",
        match_percentage=90,
        skills=["Agile"],
        education=["MBA"],
        email="target@example.com"
    )
    db_session.add(analysis)
    db_session.commit()

    # 3. Log in as attacker
    login_resp = client.post('/auth/login', data={
        "email": "attacker@example.com",
        "password": "password123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200

    # 4. Attacker attempts to fetch owner's archive
    resp = client.get(f'/archives/{analysis.id}')
    assert resp.status_code == 403
    assert "Forbidden" in resp.get_json()["error"]

    # 5. Attacker attempts to delete owner's archive
    del_resp = client.delete(f'/archives/{analysis.id}')
    assert del_resp.status_code == 403
    assert "Forbidden" in del_resp.get_json()["error"]

    # 6. Verify record still exists in DB
    db_session.expire_all()
    record = db_session.get(Analysis, analysis.id)
    assert record is not None
    assert record.candidate_name == "Target CV"
