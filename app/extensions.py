from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth

# Centralized extension instances
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
cors = CORS()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()
