import os
from werkzeug.utils import secure_filename
from flask import current_app


def save_uploaded_file(file) -> str:
    """Saves the uploaded file and returns the file path."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    return file_path
