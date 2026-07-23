"""Flask application factory for the timetable management system."""

from flask import Flask

from config import get_config


def create_app(config_name=None):
    """Create and configure a Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    return app
