from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
import uuid

from app.extensions import db, oauth
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ==========================================================================
# 1. Traditional Password Registration & Login Routes
# ==========================================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Allows new users to create accounts."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash("Email and Password are required fields.", "error")
            return render_template('auth/register.html')
            
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account already exists for this email address.", "error")
            return render_template('auth/register.html')
            
        try:
            user = User(email=email, name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash("Account registered successfully! Welcome to SynapseCV.", "success")
            return redirect(url_for('web.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to register user: {e}", exc_info=True)
            flash("An error occurred during registration. Please try again.", "error")
            
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Traditional sign in view."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash("Please fill in both email and password.", "error")
            return render_template('auth/login.html')
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email address or password.", "error")
            return render_template('auth/login.html')
            
        login_user(user)
        flash("Logged in successfully! Welcome back.", "success")
        return redirect(url_for('web.index'))
        
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Signs out active user session."""
    logout_user()
    flash("You have been signed out successfully.", "success")
    return redirect(url_for('auth.login'))


# ==========================================================================
# 2. Dual-Mode Google/Github OAuth Integration (With Simulated Developer Mode)
# ==========================================================================
@auth_bp.route('/oauth/google')
def login_google():
    """Triggers Google OAuth flow (or falls back to Sandbox Developer Mode if no Keys exist)."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        # SANDBOX DEV MODE: Render transition screen to prevent back-button loops
        current_app.logger.warning("No Google OAuth secrets detected. Running in simulated Developer Sandbox Mode.")
        return render_template('auth/sandbox_auth.html')
        
    # Standard dynamic registration
    oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
        client_kwargs={'scope': 'openid email profile'},
        server_metadata_url=current_app.config.get("GOOGLE_DISCOVERY_URL")
    )
    
    redirect_uri = url_for('auth.google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/oauth/google/authorize')
def google_authorize():
    """Handles standard Google OAuth callback authorized tokens."""
    try:
        _token = oauth.google.authorize_access_token()
        resp = oauth.google.get('userinfo')
        user_info = resp.json()
        
        email = user_info.get("email")
        name = user_info.get("name", "Google User")
        sub = user_info.get("sub", str(uuid.uuid4()))
        
        if not email:
            flash("Failed to retrieve email info from Google profile.", "error")
            return redirect(url_for('auth.login'))
            
        return handle_oauth_success(email, name, "google", sub)
    except Exception as e:
        current_app.logger.error(f"Google OAuth failed: {e}", exc_info=True)
        flash("Authentication via Google failed.", "error")
        return redirect(url_for('auth.login'))


@auth_bp.route('/oauth/sandbox', methods=['POST'])
def google_sandbox_callback():
    """Simulates success callback in developer mode for frictionless recruiter testing."""
    mock_email = "developer.sandbox@synapsecv.io"
    mock_name = "Sandbox Recruiter"
    mock_sub = "sandbox-sub-12345"
    
    flash("SANDBOX MODE: Logged in via simulated Google OAuth Developer Flow.", "success")
    return handle_oauth_success(mock_email, mock_name, "google", mock_sub)


def handle_oauth_success(email, name, provider, sub_id):
    """Binds or logs in an OAuth user account."""
    # Find existing user by provider ID or email
    user = User.query.filter((User.oauth_provider == provider) & (User.oauth_id == sub_id)).first()
    
    if not user:
        # Check if email is registered to a standard account
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Bind OAuth details
            user.oauth_provider = provider
            user.oauth_id = sub_id
            if not user.name:
                user.name = name
        else:
            # Register new OAuth user
            user = User(email=email, name=name, oauth_provider=provider, oauth_id=sub_id)
            db.session.add(user)
            
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"OAuth save failed: {e}")
            flash("Database synchronization failed.", "error")
            return redirect(url_for('auth.login'))
            
    login_user(user)
    return redirect(url_for('web.index'))
