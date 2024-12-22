from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.exceptions import InvalidAPIUsage


def register_error_handlers(app):
    """Registers custom error handlers for the application."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handles HTTP exceptions and returns a JSON response."""
        return jsonify({"message": e.description, "code": e.code}), e.code

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Handles all other uncaught exceptions and returns a JSON response."""
        app.logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify(
            {
                "message": "An internal server error occurred.",
                "error": str(e),
                "code": 500,
            }
        ), 500

    @app.errorhandler(InvalidAPIUsage)
    def handle_invalid_api_usage(e):
        """Handles InvalidAPIUsage exceptions."""
        return jsonify(e.to_dict()), e.code
