from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="Bad Request", message=str(e.description)), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify(error="Unauthorized", message=str(e.description)), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(error="Forbidden", message=str(e.description)), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not Found", message=str(e.description)), 404

    @app.errorhandler(409)
    def conflict(e):
        return jsonify(error="Conflict", message=str(e.description)), 409

    @app.errorhandler(422)
    def unprocessable_entity(e):
        return jsonify(error="Unprocessable Entity", message=str(e.description)), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(
            error="Internal Server Error", message="An unexpected error occurred."
        ), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify(error=e.name, message=e.description), e.code
