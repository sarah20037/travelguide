from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from routes import api
import os

app = Flask(__name__, static_folder='frontend')

# CORS Configuration - Allow all routes for simplicity during development
CORS(app)

# Swagger UI Setup
SWAGGER_URL = '/api/docs'
API_URL = '/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "AI Travel Planner API"}
)
app.register_blueprint(swaggerui_blueprint)

# Register API routes
app.register_blueprint(api)

# Serve Swagger spec
@app.route('/swagger.yaml')
def swagger():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'swagger.yaml')

# Serve frontend files
@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'frontend.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')