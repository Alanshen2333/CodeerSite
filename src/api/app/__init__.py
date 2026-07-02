import os
from flask import Flask
from app.config import config


def register_blueprints(app):
    """Register all API blueprints."""
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.tags import tags_bp
    from app.api.questions import questions_bp
    from app.api.answers import answers_bp
    from app.api.votes import votes_bp
    from app.api.comments import comments_bp
    from app.api.bookmarks import bookmarks_bp
    from app.api.projects import projects_bp
    from app.api.issues import issues_bp
    from app.api.milestones import milestones_bp
    from app.api.kanban import kanban_bp
    from app.api.search import search_bp
    from app.api.notifications import notifications_bp
    from app.api.admin import admin_bp
    from app.api.badges import badges_bp
    from app.api.docs import docs_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tags_bp, url_prefix="/api/tags")
    app.register_blueprint(questions_bp, url_prefix="/api/questions")
    app.register_blueprint(answers_bp, url_prefix="/api/answers")
    app.register_blueprint(votes_bp, url_prefix="/api/votes")
    app.register_blueprint(comments_bp, url_prefix="/api/comments")
    app.register_blueprint(bookmarks_bp, url_prefix="/api/bookmarks")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    # issues/milestones/kanban routes already include /api/projects/<slug>/ prefix
    app.register_blueprint(issues_bp, url_prefix="/api")
    app.register_blueprint(milestones_bp, url_prefix="/api")
    app.register_blueprint(kanban_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(badges_bp, url_prefix="/api/badges")
    app.register_blueprint(docs_bp, url_prefix="/api")


def register_error_handlers(app):
    """Register global error handlers."""
    from app.utils.errors import register_handlers
    register_handlers(app)


def create_app(config_name=None):
    """Flask application factory."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "production")

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    return app
