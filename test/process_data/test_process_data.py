import json
import os
import re
import pytest

from utils.data_processing import DataProcessing


UPLOAD_FOLDER = "test/process_data/test_data/input/"
EXPECTED_FOLDER = "test/process_data/test_data/expected/"


def process_uploaded_file(filename):
    students = DataProcessing().result_file_process(
        os.path.join(UPLOAD_FOLDER, filename)
    )

    return [student.to_dict() for student in students]


def test_invalid_file_type():
    expected_message = "Invalid file type. Expected an Excel file (.xlsx or .xls)."
    with pytest.raises(
        ValueError,
        match=re.escape(expected_message),
    ):
        process_uploaded_file("mock_unsupport.docx")


def test_missing_columns():
    with pytest.raises(ValueError, match="Missing required columns: F_TEN"):
        process_uploaded_file("mock_missing_columns.xlsx")


def test_successfully_read():
    input_file = "mock_result.xlsx"
    expected_file = os.path.join(EXPECTED_FOLDER, "test_successfully_read.json")

    result = process_uploaded_file(input_file)

    with open(expected_file, "r") as file:
        expected_result = json.load(file)

    assert result == expected_result


def test_missing_null_data():
    input_file = "mock_missing_data.xlsx"
    expected_file = os.path.join(EXPECTED_FOLDER, "test_missing_null_data.json")

    result = process_uploaded_file(input_file)

    with open(expected_file, "r") as file:
        expected_result = json.load(file)

    assert result == expected_result
