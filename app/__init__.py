"""
Sugartalking AVR Control Application

A universal web-based control interface for Audio/Video Receivers (AVRs)
with support for multiple manufacturers and models.
"""

__version__ = '2.0.0'
__author__ = 'Sugartalking Project'

from flask import Flask
from flask_cors import CORS
import logging
import os


def create_app(config=None):
    """
    Application factory for creating Flask app instances.

    Args:
        config: Configuration dictionary

    Returns:
        Configured Flask application
    """
    app = Flask(__name__, static_folder='../static', static_url_path='')

    # Load configuration
    if config:
        app.config.update(config)

    # Enable CORS
    CORS(app)

    # Setup logging
    setup_logging(app)

    # Initialize database
    from app.models import init_db
    init_db()

    # Register blueprints
    from app.routes import api, admin, web
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(web.bp)

    return app


def setup_logging(app):
    """
    Configure application logging.

    Args:
        app: Flask application
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_dir = os.getenv('LOG_DIR', '/data/logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'sugartalking.log')

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # stdout for kubectl logs
            logging.FileHandler(log_file)  # file for persistence
        ]
    )

    app.logger.setLevel(getattr(logging, log_level))
    app.logger.info(f"Sugartalking v{__version__} initialized")
