from flask import Blueprint, request, jsonify
from utils.file_handling import save_uploaded_file, read_and_prepare_data
from utils.data_processing import process_data

irt_analyze = Blueprint('irt_analyze', __name__)

@irt_analyze.route('/api/irt/analyze', methods=['POST'])
def analyze_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({'error': 'Invalid file type. Only Excel files are allowed.'}), 400

    try:
        # Save and process the uploaded file
        file_path = save_uploaded_file(file)
        df = read_and_prepare_data(file_path)
        analysis_results = process_data(df)

        return jsonify(analysis_results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
