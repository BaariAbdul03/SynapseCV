from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

from app.extensions import db

class User(db.Model, UserMixin):
    """User Model representing candidates or recruiters."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)  # Nullable for OAuth users
    
    # OAuth Integration
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_id = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to candidate analyses
    analyses = db.relationship('Analysis', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Generates password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Validates input password against hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Analysis(db.Model):
    """Analysis Model representing parsed candidate resume profiles against criteria."""
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    
    # Candidate details
    candidate_name = db.Column(db.String(150), nullable=True)
    detected_role = db.Column(db.String(100), nullable=True)
    match_percentage = db.Column(db.Integer, default=0)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    
    # Lists stored as serialized JSON strings for database platform compatibility (SQLite/PostgreSQL)
    _education = db.Column('education', db.Text, nullable=True)
    _skills = db.Column('skills', db.Text, nullable=True)
    _missing_keywords = db.Column('missing_keywords', db.Text, nullable=True)
    
    profile_summary = db.Column(db.Text, nullable=True)
    scoring_reasoning = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Property Getters / Setters to handle serialization transparently ---
    @property
    def education(self):
        if not self._education:
            return []
        try:
            return json.loads(self._education)
        except Exception:
            return []

    @education.setter
    def education(self, value):
        self._education = json.dumps(value if value is not None else [])

    @property
    def skills(self):
        if not self._skills:
            return []
        try:
            return json.loads(self._skills)
        except Exception:
            return []

    @skills.setter
    def skills(self, value):
        self._skills = json.dumps(value if value is not None else [])

    @property
    def missing_keywords(self):
        if not self._missing_keywords:
            return []
        try:
            return json.loads(self._missing_keywords)
        except Exception:
            return []

    @missing_keywords.setter
    def missing_keywords(self, value):
        self._missing_keywords = json.dumps(value if value is not None else [])

    def to_dict(self):
        """Serializes DB model into API-ready dictionary."""
        return {
            "id": self.id,
            "name": self.candidate_name,
            "detected_role": self.detected_role,
            "match_percentage": self.match_percentage,
            "email": self.email,
            "phone": self.phone,
            "github_url": self.github_url,
            "linkedin_url": self.linkedin_url,
            "education": self.education,
            "skills": self.skills,
            "missing_keywords": self.missing_keywords,
            "profile_summary": self.profile_summary,
            "scoring_reasoning": self.scoring_reasoning,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<Analysis {self.id} - {self.candidate_name} ({self.match_percentage}%)>"


class ApiKey(db.Model):
    """ApiKey Model representing API credentials for developer accounts."""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), default="Production API Key")
    key_prefix = db.Column(db.String(10), nullable=False)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('api_keys', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ApiKey {self.key_prefix}xxxx - {self.name}>"


class RoleTemplate(db.Model):
    """RoleTemplate Model storing recruiter-defined target templates."""
    __tablename__ = 'role_templates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True) # Null = global template
    role_name = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('role_templates', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<RoleTemplate {self.role_name} (User: {self.user_id})>"
