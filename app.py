from flask import Flask

from routes.ctt_analyze import ctt_analyze
from utils.error_handlers import register_error_handlers

import logging

# Configure logging
logging.basicConfig(
    filename="app.log",  # Specify the log file name
    filemode="a",  # Append mode ('a' for append, 'w' for overwrite)
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)


app = Flask(__name__)

# Load configurations
app.config.from_object("config")
app.json.sort_keys = False
register_error_handlers(app)

# Register Blueprints or routes
app.register_blueprint(ctt_analyze, url_prefix="/api/analyze")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
