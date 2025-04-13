from flask import Blueprint, request, jsonify
import jwt
import os
import logging
from services.analyze import AnalysisService
from utils.exceptions import InvalidAPIUsage

analyze = Blueprint("analyze", __name__)
analysis_service = AnalysisService()


@analyze.route("/<string:analysis_type>", methods=["POST"])
def analyze_file(analysis_type):
    if analysis_type.lower() not in ["ctt", "rasch"]:
        raise InvalidAPIUsage(
            "Invalid analysis type. Must be 'ctt' or 'rasch'", code=400
        )

    required_files = ["result_file", "exam_file"]

    # Validate file existence
    for file_key in required_files:
        if file_key not in request.files:
            raise InvalidAPIUsage(f"Missing file: {file_key}", code=400)

    uploaded_files = {file_key: request.files[file_key] for file_key in required_files}

    # Extract form fields
    project_name = request.form.get("projectName")
    number_of_group = request.form.get("numberOfGroup")
    group_percentage = request.form.get("groupPercentage")
    correlation_rpbis = request.form.get("correlationRpbis")

    token = request.cookies.get("auth_token")
    if not token:
        raise InvalidAPIUsage("Unauthorized: Missing authentication token", code=401)

    try:
        decoded_token = jwt.decode(
            token,
            os.getenv("SUPABASE_JWT_SECRET"),
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = decoded_token.get("sub")
        if not user_id:
            raise InvalidAPIUsage("Forbidden: Invalid token payload", code=403)

        logging.info(f"Authenticated request by user_id: {user_id}")

        # Analyze
        analysis_service.analyze_uploaded_file(
            result_file=uploaded_files["result_file"],
            exam_file=uploaded_files["exam_file"],
            analysis_method=analysis_type,
        )

        sorted_students, _, _ = analysis_service.analysis.split_students()
        if analysis_type == "Rasch":
            res = analysis_service.save_rasch_analysis_to_supabase(
                project_name,
                number_of_group,
                group_percentage,
                correlation_rpbis,
                analysis_service.analysis.rasch_analysis(),
                sorted_students,
                analysis_service.analysis.average_indexes,
                user_id,
            )
        else:  # "ctt"
            res = analysis_service.save_analysis_to_supabase(
                project_name,
                number_of_group,
                group_percentage,
                correlation_rpbis,
                analysis_service.get_analysis_results(),
                sorted_students,
                analysis_service.get_average_indexes(),
                user_id,
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
