from flask import Blueprint
from flask_cors import CORS

api = Blueprint('api_v1', __name__)

from . import views