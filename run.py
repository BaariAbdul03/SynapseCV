import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Default to port 5000, debug mode determined by environment config
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
