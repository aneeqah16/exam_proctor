from flask import Blueprint

proctoring_bp = Blueprint("proctoring", __name__)

from . import routes