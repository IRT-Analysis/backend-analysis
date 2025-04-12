import json
import os
from itertools import groupby
import uuid

import pandas as pd

from models.exam import Exam
from models.exam_result import ExamResult
from models.question import Option, QuestionBank
from utils.data_processing import DataProcessing
from analysis.ctt_analysis import CttAnalysis
from analysis.irt_analysis import IrtAnalysis
from analysis.method import Method
from services.analyze import AnalysisService
import requests
import jwt
import os
from dotenv import load_dotenv
from utils.data_processing import DataProcessing
from services.analyze import AnalysisService

UPLOAD_FOLDER = "uploads/"
data_processing = DataProcessing()
service = AnalysisService()
load_dotenv()


UPLOAD_FOLDER = "uploads/"


def analyze_uploaded_file():
    # Save and process the uploaded file

    # Load Question Bank
    question_bank = QuestionBank()
    # question_bank_df = pd.read_csv(
    #     os.path.join(UPLOAD_FOLDER, "mock_question_bank_items.csv")
    # )
    # question_bank_data = question_bank_df.to_dict(orient="records")
    exam_df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "mock_exam_items.csv"))
    exam_data = exam_df.to_dict(orient="records")
    question_id = 0
    exam_code = exam_data[1]["Exam_code"]

    for question in exam_data:
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

    # Process Students' Results
    students = DataProcessing().result_file_process(
        os.path.join(UPLOAD_FOLDER, "KQCO2003.xlsx")
    )

    # Process Exam Data
    # exam_df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "mock_exam_items.csv"))
    # exam_data = exam_df.to_dict(orient="records")
    exams = process_exam(exam_data, question_bank)

    # Generate Exam Results and Analysis
    exam_result = ExamResult(exams, students)
    # analysis = CttAnalysis(exam_result)
    analysis = IrtAnalysis(exam_result)
    getData = Method()
    # service = AnalysisService(exam_result, getData)
    analysis.get_model("Rasch")
    analysis.rasch_analysis()
    student_list = []
    student_list.append(student.to_dict() for student in exam_result.students)
    # analysis.get_model("Rasch")
    service = AnalysisService()
    service.getData = getData
    service.exam_result = exam_result
    service.analysis = analysis

    service.save_rasch_analysis_to_supabase(
        project_name="Test Project",
        number_of_group=3,
        group_percentage=[0.3, 0.5, 0.2],
        correlation_rpbis={},
        analysis_data=analysis.rasch_analysis(),
        student_answer_data=student_list,
        average_indexes=analysis.average_indexes,
        user_id="4ea08a4b-470e-4bd1-a780-8b599bacb084",
    )


def process_exam(file_path, question_bank):
    # Group data by Exam_code
    file_path.sort(key=lambda x: x["Exam_code"])

    # Group the data by 'Exam_code'
    grouped = {
        key: list(group)
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
                    for index, option in enumerate(options):
                        for option_bank in question_data["options"]:
                            # print(option, " " , option_bank.content)
                            if option == option_bank.content:
                                matched_answer_order[index] = option_bank
                                break

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


def writeJson(data, output_file="analysis_result.json"):
    output_file = output_file

    with open(output_file, "w") as json_file:
        json.dump(data, json_file, indent=4)  # indent=4 for pretty-printing the JSON

    print(f"Analysis result has been written to {output_file}")


analyze_uploaded_file()
