import logging
from flask import Blueprint, request, jsonify
from services.analyze import CttService
from utils.exceptions import InvalidAPIUsage

ctt_analyze = Blueprint("ctt_analyze", __name__)
ctt_service = CttService()


@ctt_analyze.route("/ctt", methods=["POST"])
def analyze_file():
    if "file" not in request.files:
        raise InvalidAPIUsage("No file uploaded", code=400)

    file = request.files["file"]
    if not file.filename.endswith((".xls", ".xlsx")):
        raise InvalidAPIUsage(
            "Invalid file type. Only Excel files are allowed.", code=400
        )

    try:
        # Delegate to the service layer
        ctt_service.analyze_uploaded_file(file)

        return jsonify(
            {
                "message": "File uploaded and processed successfully.",
                "data": "asb2s",
                "code": 201,
            }
        ), 201

    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        raise InvalidAPIUsage("Required file missing", code=404)
    except ValueError as e:
        logging.error(f"Value error: {str(e)}")
        raise InvalidAPIUsage("Invalid file content", code=400)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise InvalidAPIUsage("An unexpected error occurred", code=500, error=e)


@ctt_analyze.route("/ctt/<analysis_id>", methods=["GET"])
def get_analysis_results(analysis_id):
    """
    Endpoint to retrieve the analysis results.
    """
    try:
        result = ctt_service.get_analysis_results()
        return jsonify(
            {
                "message": f"Analysis {analysis_id} results retrieved successfully.",
                "data": result,
            }
        ), 200
    except FileNotFoundError:
        raise InvalidAPIUsage(f"Analysis {analysis_id} not found.", code=404)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise InvalidAPIUsage("An unexpected error occurred", code=500, error=e)


@ctt_analyze.route("/ctt/<analysis_id>/general-detail", methods=["GET"])
def get_general_detail(analysis_id):
    """
    Endpoint to retrieve general details about the analysis.
    """
    try:
        general_detail = ctt_service.get_general_detail()
        return jsonify(
            {
                "message": f"Analysis {analysis_id} general detail retrieved successfully.",
                "data": general_detail,
                "code": 200,
            }
        ), 200
    except FileNotFoundError:
        raise InvalidAPIUsage(
            f"General details for analysis {analysis_id} not found.", code=404
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise InvalidAPIUsage("An unexpected error occurred", code=500, error=e)


@ctt_analyze.route("/ctt/question/<int:question_id>", methods=["GET"])
def get_question_stats(question_id):
    """
    Endpoint to retrieve stats for a specific question.
    """
    try:
        question_stats = ctt_service.get_question_stats(question_id)
        return jsonify(
            {
                "message": "Question stats retrieved successfully.",
                "data": question_stats,
                "code": 200,
            }
        ), 200
    except FileNotFoundError:
        raise InvalidAPIUsage(f"Stats for question {question_id} not found.", code=404)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise InvalidAPIUsage("An unexpected error occurred", code=500, error=e)


@ctt_analyze.route("/ctt/<analysis_id>/average-detail", methods=["GET"])
def get_average_indexes(analysis_id):
    """
    Endpoint to retrieve average indexes from the analysis.
    """
    try:
        average_indexes = ctt_service.get_average_indexes()
        return jsonify(
            {
                "message": f"{analysis_id} average indexes retrieved successfully.",
                "data": average_indexes,
                "code": 200,
            }
        ), 200
    except FileNotFoundError:
        raise InvalidAPIUsage(
            f"Average indexes for analysis {analysis_id} not found.", code=404
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise InvalidAPIUsage("An unexpected error occurred", code=500, error=e)
