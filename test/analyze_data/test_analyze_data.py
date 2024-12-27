from itertools import groupby
import json
import os
import pandas as pd

from analysis.ctt_analysis import CttAnalysis
from models.exam import Exam
from models.exam_result import ExamResult
from models.question import Option, QuestionBank
from utils.data_processing import DataProcessing


UPLOAD_FOLDER = "test/analyze_data/test_data/input/"
EXPECTED_FOLDER = "test/analyze_data/test_data/expected/"


def process_exam(file_path, question_bank):
    # Group data by Exam_code
    file_path.sort(key=lambda x: x["Exam_code"])

    # Group the data by 'Exam_code'
    grouped = {
        key: list(file_path)
        for key, group in groupby(file_path, key=lambda x: x["Exam_code"])
    }

    exams = []

    for exam_code, group in grouped.items():
        question_order = []
        answer_order = {}

        for question in group:
            content = question["Content"]
            options = [
                question["Option_A"],
                question["Option_B"],
                question["Option_C"],
                question["Option_D"],
            ]
            correct_option = question["Correct_Option"]

            # Match content with the question bank
            matched_question_id = None
            matched_answer_order = [None] * 4

            for question_id, question_data in question_bank.get_all_questions().items():
                if question_data["content"] == content:
                    matched_question_id = question_id
                    matched_answer_order = question_data["options"]
                    # for idx, option in enumerate(options):
                    #     # if option in question_data['options']:
                    #     matched_answer_order[idx] = question_data['options'].index(option)
                    # break

            if matched_question_id is None:
                print(
                    f"Warning: Question not found in question bank for Exam Code {exam_code}: {content}"
                )
                continue

            # Append question order and answer order
            question_order.append(matched_question_id)
            answer_order[matched_question_id] = matched_answer_order

        # Initialize Exam object
        exam = Exam(
            code=exam_code,
            question_bank=question_bank,
            question_order=question_order,
            answer_order=answer_order,
        )

        exams.append(exam)

    return exams


def analyze_data(filename, exam_items, question_bank_path):
    question_bank = QuestionBank()
    question_bank_df = pd.read_csv(os.path.join(UPLOAD_FOLDER, question_bank_path))
    question_bank_df = question_bank_df.question_bank_df.groupby('Exam_code')
    question_bank_data = question_bank_df.to_dict(orient="records")
    question_id = 0
    exam_code = question_bank_df[1]["Exam_code"]
    for question in question_bank_data:
        if question["Exam_code"] == exam_code:
            question_id = question_id + 1
            question_content = question["Content"]
            options = [
                Option(question["Option_A"]),
                Option(question["Option_B"]),
                Option(question["Option_C"]),
                Option(question["Option_D"]),
            ]
            correct_answer = question["Correct_Option"]
            correct_answer_index = ["A", "B", "C", "D"].index(correct_answer)

            question_bank.add_question(
                question_id, question_content, options, correct_answer_index
            )
        else:
            break

    students = DataProcessing().result_file_process(
        os.path.join(UPLOAD_FOLDER, filename)
    )

    exam_df = pd.read_csv(os.path.join(UPLOAD_FOLDER, exam_items))
    exam_data = exam_df.to_dict(orient="records")

    exams = process_exam(exam_data, question_bank)

    exam_result = ExamResult(exams, students)
    return CttAnalysis(exam_result).analyze_questions_ctt()


def compare_dicts(actual, expected, tolerance=0.01):
    """
    Recursively compares two dictionaries, handling numerical and categorical values.
    Raises AssertionError if a mismatch is found.

    Args:
        actual (dict): The actual dictionary to compare.
        expected (dict): The expected dictionary to compare.
        tolerance (float): Tolerance for numerical comparisons.
    """
    # Normalize keys to strings for consistent comparison
    actual = {str(key): value for key, value in actual.items()}
    expected = {str(key): value for key, value in expected.items()}

    for key, expected_value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual data"

        actual_value = actual[key]

        if isinstance(expected_value, dict):
            assert isinstance(actual_value, dict), f"Key '{key}' should be a dictionary"
            compare_dicts(actual_value, expected_value, tolerance)
        elif isinstance(expected_value, (int, float)):
            assert (
                abs(float(actual_value) - float(expected_value)) < tolerance
            ), f"Mismatch for key '{key}': expected {expected_value}, got {actual_value}"
        else:
            assert (
                actual_value == expected_value
            ), f"Mismatch for key '{key}': expected '{expected_value}', got '{actual_value}'"


def wrapper(
    input_file,
    output_file,
    exam_items="mock_exam_items.csv",
    question_bank_path="mock_question_bank_items.csv",
):
    with open(os.path.join(EXPECTED_FOLDER, output_file), "r") as json_file:
        expected_output = json.load(json_file)

    result = analyze_data(input_file, exam_items, question_bank_path)

    for question, expected_metrics in expected_output.items():
        assert question in result, f"Question '{question}' not found in actual data"
        compare_dicts(result[question], expected_metrics)


def test_all_valid_response():
    wrapper("mock_result.xlsx", "test_valid_input.json")


def test_missing_responses():
    wrapper("mock_missing_data.xlsx", "test_missing_responses.json")


def test_uniform_responses():
    wrapper("mock_uniform_response.xlsx", "test_uniform_responses.json")


def test_large_data_set():
    wrapper(
        "mock_result-large.xlsx",
        "test_large_data_set.json",
        "mock_exam_items-large.csv",
        "mock_question_bank_items-large.csv",
    )
