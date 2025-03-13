from flask import Flask
from .api import api as api_blueprint
from .views import main as main_blueprint
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, supports_credentials=True)
    # # Define the upload folder path
    # UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    # app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # # Ensure the uploads directory exists
    # os.makedirs(UPLOAD_FOLDER, exist_ok=True)


    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    app.register_blueprint(main_blueprint)
    # cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    # CORS(app, origins=[os.getenv("CLIENT_URL")])
    
    # print("CLIENT_ORIGIN:", os.getenv("CLIENT_ORIGIN"))
    # client_origin = os.getenv("CLIENT_URL", "http://localhost:3000")
    # CORS(app, origins=[client_origin]) 

    
    return app