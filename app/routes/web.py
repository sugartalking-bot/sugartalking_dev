"""
Web routes for serving the frontend.
"""

from flask import Blueprint, send_from_directory
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('web', __name__)


@bp.route('/')
def index():
    """Serve the main web interface."""
    logger.info("Serving web interface")
    return send_from_directory('../static', 'index.html')
