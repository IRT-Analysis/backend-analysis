import json
import os

# from data_processing import DataProcessing
from itertools import groupby

import pandas as pd
from data_processing import DataProcessing
from data_structure.exam import Exam
from data_structure.examResult import ExamResult
from data_structure.option import Option
from data_structure.question import QuestionBank
from data_structure.student import Student
from method.ctt_analysis import CttAnalysis

from config import UPLOAD_FOLDER

# question_bank_df = pd.read_csv(
#     os.path.join(UPLOAD_FOLDER, "mock_question_bank_items.csv")
# )

# # Convert the DataFrame into a list of dictionaries
# question_bank_data = question_bank_df.to_dict(orient="records")

# print("Exam Data:", len(question_bank_data))  # Display the first 5 records


# # Tạo bộ câu hỏi chuẩn
# question_bank = QuestionBank()

# for question in question_bank_data:
#     question_id = question["Question_ID"]
#     question_content = question["Content"]
#     # options = [question['Option_A'], question['Option_B'], question['Option_C'], question['Option_D']]
#     options = [
#         Option(question["Option_A"]),
#         Option(question["Option_B"]),
#         Option(question["Option_C"]),
#         Option(question["Option_D"]),
#     ]
#     correct_answer = question["Correct_Option"]
#     correct_answer_index = ["A", "B", "C", "D"].index(correct_answer)

#     # Add the question to the QuestionBank
#     question_bank.add_question(
#         question_id, question_content, options, correct_answer_index
#     )


# # Now the question bank contains the questions
# print(question_bank.get_all_questions())
student_results_data = [
    {
        "Student_ID": "S001",
        "First_Name": "John",
        "Last_Name": "Doe",
        "Exam_code": "EX001",
        "Q001": "B1",
        "Q002": "A1",
        "Q003": "BS",
        "Q004": "DS",
    },
    {
        "Student_ID": "S002",
        "First_Name": "Jane",
        "Last_Name": "Smith",
        "Exam_code": "EX001",
        "Q1": "AS",
        "Q2": "B1",
        "Q3": "C1",
        "Q4": "DS",
    },
    {
        "Student_ID": "S003",
        "First_Name": "Bob",
        "Last_Name": "Lee",
        "Exam_code": "EX002",
        "Q1": "A1",
        "Q2": "B1",
        "Q3": "C1",
        "Q4": "D1",
    },
    {
        "Student_ID": "S004",
        "First_Name": "Emily",
        "Last_Name": "White",
        "Exam_code": "EX002",
        "Q1": "AS",
        "Q2": "B1",
        "Q3": "C1",
        "Q4": "DS",
    },
]


def process_student_results(student_results_data, question_bank):
    students = []

    # Iterate over each student's result in the data
    for student_data in student_results_data:
        # Extract student information
        student_id = student_data["Student_ID"]
        first_name = student_data["First_Name"]
        last_name = student_data["Last_Name"]
        exam_code = student_data["Exam_code"]

        # Prepare the answers dictionary
        answers = {}

        for key, value in student_data.items():
            if key.startswith("Q"):  # Only process the questions (Q1, Q2, etc.)
                question_id = key  # e.g., 'Q1'

                # Determine the answer and correctness
                answer_value = value[:-1]  # Get the answer part (A, B, C, etc.)
                is_correct = False
                if value.endswith("1"):
                    is_correct = True
                elif value.endswith("S"):
                    is_correct = False
                elif value == "":  # For unanswered questions
                    is_correct = None

                # Convert the answer letter to an index (0 for A, 1 for B, etc.)
                option_index = ["A", "B", "C", "D"].index(answer_value)
                # Store answer in the dictionary with the new structure
                answers[question_id] = {
                    "answer": option_index,  # Answer as index list (can be extended if needed)
                    "correct": is_correct,
                }

        # Create a Student object
        student = Student(student_id, first_name, last_name, exam_code, answers)
        students.append(student)

    return students


# Process the student results and create Student objects
# students = process_student_results(student_results_data, question_bank_data)


# def student_to_dict(student):
#     return {
#         "Student_ID": student.id,
#         "First_Name": student.firstName,
#         "Last_Name": student.lastName,
#         "Exam_code": student.exam_code,
#         "Answers": student.answers,
#     }


# # Use list comprehension to serialize all Student objects
# students_data = [student_to_dict(student) for student in students]

# # Specify the output JSON file path
# output_file = "students_results.json"

# # Write the data to the JSON file
# with open(output_file, "w") as json_file:
#     json.dump(students_data, json_file, indent=4)  # Pretty-printing the JSON

# print(f"Student results have been written to {output_file}")

# ====== PROCESS STUDENT DATA FROM FILE ======
# file_path = "./uploads/KQCO2003.xlsx"
# students = DataProcessing().result_file_process(file_path)


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


# exam_file_data = [
#     {
#         "Exam_code": "EX001",
#         "Content": "What is the capital of France?",
#         "Option_A": "London",
#         "Option_B": "Paris",
#         "Option_C": "Berlin",
#         "Option_D": "Rome",
#         "Correct_Option": "B",
#     },
#     {
#         "Exam_code": "EX001",
#         "Content": "What is 2+2?",
#         "Option_A": "4",
#         "Option_B": "5",
#         "Option_C": "6",
#         "Option_D": "3",
#         "Correct_Option": "A",
#     },
#     {
#         "Exam_code": "EX002",
#         "Content": "What is 3+5?",
#         "Option_A": "7",
#         "Option_B": "8",
#         "Option_C": "9",
#         "Option_D": "10",
#         "Correct_Option": "B",
#     },
#     {
#         "Exam_code": "EX002",
#         "Content": "What is the largest ocean?",
#         "Option_A": "Atlantic",
#         "Option_B": "Indian",
#         "Option_C": "Arctic",
#         "Option_D": "Pacific",
#         "Correct_Option": "D",
#     },
#     {
#         "Exam_code": "EX002",
#         "Content": "What is 2+2?",
#         "Option_A": "4",
#         "Option_B": "5",
#         "Option_C": "6",
#         "Option_D": "3",
#         "Correct_Option": "A",
#     },
#     {
#         "Exam_code": "EX002",
#         "Content": "What is the capital of France?",
#         "Option_A": "London",
#         "Option_B": "Paris",
#         "Option_C": "Berlin",
#         "Option_D": "Rome",
#         "Correct_Option": "B",
#     },
# ]


# # Read the CSV file into a pandas DataFrame


# students = DataProcessing().result_file_process(
#     os.path.join(UPLOAD_FOLDER, "KQCO2003.xlsx")
# )


# exam_df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "mock_exam_items.csv"))

# # # Convert the DataFrame into a list of dictionaries
# exam_data = exam_df.to_dict(orient="records")


# exams = process_exam(exam_data, question_bank)


# examResult = ExamResult(exams, students)

# analysis = CttAnalysis(examResult)


# output_file = "./analysis_result.json"

# with open("./student.json", "w") as json_file:
#     for student in students:
#         json.dump(
#             [student.id, student.answers], json_file, indent=4
#         )  # indent=4 for pretty-printing the JSON
# with open("./exam.json", "w") as json_file:
#     for score in examResult.scores:
#         json.dump(
#             [score["student"].id, score["score"]], json_file, indent=4
#         )  # indent=4 for pretty-printing the JSON


# # Open the file in write mode and dump the result into it
# with open(output_file, "w") as json_file:
#     json.dump(
#         analysis.analyze_questions_ctt(), json_file, indent=4
#     )  # indent=4 for pretty-printing the JSON

# print(f"Analysis result has been written to {output_file}")
