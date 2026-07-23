"""Flask application factory for the timetable management system."""

from flask import Flask

from config import get_config
from app.auth import get_current_user


def create_app(config_name=None):
    """Create and configure a Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.professors import professors_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(professors_bp)
    app.context_processor(lambda: {"current_user": get_current_user()})
    return app
