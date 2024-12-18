import os
import pandas as pd
from config import UPLOAD_FOLDER
from utils.file_handling import save_uploaded_file
from utils.data_processing import DataProcessing
from utils.exam_helpers import process_exam
from models.question_bank import QuestionBank
from models.option import Option
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
