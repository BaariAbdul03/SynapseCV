import time
import threading
from sqlalchemy import text
from app.extensions import db

def run_db_ping(app):
    """Periodically executes a lightweight SQL query to keep Supabase DB warm and active."""
    # Wait 1 minute on startup to allow app to fully initialize
    time.sleep(60)
    
    logger = app.logger
    logger.info("Database Keep-Alive service successfully started.")
    
    while True:
        try:
            with app.app_context():
                # Execute a simple, highly efficient ping query
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                logger.info("Keep-Alive database ping executed successfully. Connection is warm.")
        except Exception as e:
            logger.error(f"Keep-Alive database ping failed: {e}")
            
        # Sleep for 12 hours before next ping
        time.sleep(12 * 60 * 60)

def start_keep_alive(app):
    """Spawns the keep-alive ping runner in a low-priority daemon thread."""
    thread = threading.Thread(target=run_db_ping, args=(app,), daemon=True)
    thread.name = "SynapseCV-KeepAlive-Thread"
    thread.start()
