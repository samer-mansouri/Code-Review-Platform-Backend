from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({"error": e.name, "message": e.description}), e.code

    @app.errorhandler(413)
    def handle_large_file(e):
        return jsonify({"error": "File too large", "message": "Maximum upload size exceeded"}), 413

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        return jsonify({"error": "Server Error", "message": str(e)}), 500