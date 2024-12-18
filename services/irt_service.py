from itertools import groupby
import os
import pandas as pd
from config import UPLOAD_FOLDER
from models.exam import Exam
from models.question import Option, QuestionBank
from utils.file_handling import save_uploaded_file
from utils.data_processing import DataProcessing

from models.exam_result import ExamResult
from utils.method.ctt_analysis import CttAnalysis


def analyze_uploaded_file(file):
    # Save and process the uploaded file
    file_path = save_uploaded_file(file)

    # Load Question Bank
    question_bank = QuestionBank()
    question_bank_df = pd.read_csv(
        os.path.join(UPLOAD_FOLDER, "mock_question_bank_items.csv")
    )
    question_bank_data = question_bank_df.to_dict(orient="records")

    for question in question_bank_data:
        question_id = question["Question_ID"]
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

    # Process Students' Results
    students = DataProcessing().result_file_process(file_path)

    # Process Exam Data
    exam_df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "mock_exam_items.csv"))
    exam_data = exam_df.to_dict(orient="records")
    exams = process_exam(exam_data, question_bank)

    # Generate Exam Results and Analysis
    exam_result = ExamResult(exams, students)
    analysis = CttAnalysis(exam_result)

    return analysis.analyze_questions_ctt()


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
