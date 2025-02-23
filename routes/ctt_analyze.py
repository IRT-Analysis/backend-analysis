import logging
from flask import Blueprint, request, jsonify
from services.analyze import CttService
from testing import writeJson
from utils.exceptions import InvalidAPIUsage

ctt_analyze = Blueprint("ctt_analyze", __name__)
ctt_service = CttService()


@ctt_analyze.route("/ctt", methods=["POST"])
def analyze_file():
    required_files = ["result_file", "exam_file"]

    # Check if all required files are present in the request
    for file_key in required_files:
        if file_key not in request.files:
            raise InvalidAPIUsage(f"Missing file: {file_key}", code=400)

    # Validate file extensions and collect files
    uploaded_files = {}
    for file_key in required_files:
        file = request.files[file_key]
        # if not file.filename.endswith((".xls", ".xlsx")):
        #     raise InvalidAPIUsage(
        #         f"Invalid file type for {file_key}. Only Excel files are allowed.",
        #         code=400,
        #     )
        uploaded_files[file_key] = file

    try:
        # Delegate to the service layer and pass all files
        ctt_service.analyze_uploaded_file(
            result_file=uploaded_files["result_file"],
            exam_file=uploaded_files["exam_file"],
        )
        analysis_data = ctt_service.get_analysis_results()
        student_answer_data = ctt_service.get_student_answer()
        ctt_service.save_analysis_to_supabase(
            analysis_data, student_answer_data, ctt_service.get_average_indexes()
        )

        return jsonify(
            {
                "message": "File uploaded and saved successfully.",
                "data": "asns",
                # "data": {"analysis": result, "student_answer": student_answer},
                "code": 200,
            }
        ), 200

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
        score_historgram = ctt_service.get_score_histogram()
        discrimination_histogram = ctt_service.get_discrimination_histogram()
        difficulty_histogram = ctt_service.get_difficultiy_histogram()
        r_pbis_histogram = ctt_service.get_rpbis_histogram()
        average = ctt_service.get_average_indexes()
        histogram = {
            "score": score_historgram,
            "discrimination": discrimination_histogram,
            "difficulty": difficulty_histogram,
            "r_pbis": r_pbis_histogram,
        }

        return jsonify(
            {
                "message": f"Analysis {analysis_id} general detail retrieved successfully.",
                "data": {
                    "general": general_detail,
                    "histogram": histogram,
                    "average": average,
                },
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
