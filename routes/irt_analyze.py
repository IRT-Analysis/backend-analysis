import logging
from flask import Blueprint, request, jsonify
from services.irt_service import analyze_uploaded_file

irt_analyze = Blueprint("irt_analyze", __name__)


@irt_analyze.route("/api/irt/analyze", methods=["POST"])
def analyze_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith((".xls", ".xlsx")):
        return jsonify(
            {"error": "Invalid file type. Only Excel files are allowed."}
        ), 400

    try:
        # Delegate to the service layer
        result = analyze_uploaded_file(file)
        return jsonify(result), 200

    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        return jsonify({"error": "Required file missing"}), 404
    except ValueError as e:
        logging.error(f"Value error: {str(e)}")
        return jsonify({"error": "Invalid file content"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
