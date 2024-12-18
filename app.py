from flask import Flask

from routes.ctt_analyze import ctt_analyze

app = Flask(__name__)

# Load configurations
app.config.from_object("config")
app.json.sort_keys = False

# Register Blueprints or routes
app.register_blueprint(ctt_analyze, url_prefix="/api/analyze")

if __name__ == "__main__":
    app.run(debug=True)
