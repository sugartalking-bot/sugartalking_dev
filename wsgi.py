"""
WSGI entry point for Sugartalking application.

This module creates the Flask app instance for production WSGI servers like Gunicorn.
"""

import os
import logging

# Configure logging before importing app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import app factory
from app import create_app

# Create application instance
logger.info("Creating Flask application...")
app = create_app()

# Initialize database and seed if needed
def init_database():
    """Initialize and seed database on startup."""
    from app.models import get_session
    from scripts.seed_database import seed_denon_x2300w

    try:
        session = get_session()
        # Check if database is empty
        from app.models import Receiver
        count = session.query(Receiver).count()

        if count == 0:
            logger.info("Database is empty, seeding with initial data...")
            seed_denon_x2300w(session)
        else:
            logger.info(f"Database already contains {count} receiver model(s)")

        session.close()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)

# Initialize on startup
init_database()

logger.info("Sugartalking WSGI application ready")

if __name__ == '__main__':
    # For development/testing
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
