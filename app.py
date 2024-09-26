from flask import Flask
from routes.irt_analyze import irt_analyze

app = Flask(__name__)

# Load configurations
app.config.from_object('config')

# Register Blueprints or routes
app.register_blueprint(irt_analyze)

if __name__ == '__main__':
    app.run(debug=True)
