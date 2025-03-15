import logging
from flask import Blueprint, request, jsonify
from services.analyze import AnalysisService
from utils.exceptions import InvalidAPIUsage

analyze = Blueprint("analyze", __name__)
analysis_service = AnalysisService()


@analyze.route("/", methods=["POST"])
def analyze_file():
    required_files = ["result_file", "exam_file"]
    method = request.args.get("type")

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
    # Extract additional data from request form
    project_name = request.form.get("projectName")
    number_of_group = request.form.get("numberOfGroup")
    group_percentage = request.form.get("groupPercentage")
    correlation_rpbis = request.form.get("correlationRpbis")

    try:
        # Delegate to the service layer and pass all files
        analysis_service.analyze_uploaded_file(
            result_file=uploaded_files["result_file"],
            exam_file=uploaded_files["exam_file"],
            analysis_method=method,
        )
        analysis_data = analysis_service.get_analysis_results()
        student_answer_data = analysis_service.get_student_answer()

        res = analysis_service.save_analysis_to_supabase(
            project_name,
            number_of_group,
            group_percentage,
            correlation_rpbis,
            analysis_data,
            student_answer_data,
            analysis_service.get_average_indexes(),
        )

        return jsonify(res), 200

    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        raise InvalidAPIUsage("Required file missing", code=404)
    except ValueError as e:
        logging.error(f"Value error: {str(e)}")
        raise InvalidAPIUsage("Invalid file content", code=400)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise InvalidAPIUsage("An unexpected error occurred", code=500, error=e)
