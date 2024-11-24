import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import current_app
from data_structure.student import Student 

def save_uploaded_file(file) -> str:
    """Saves the uploaded file and returns the file path."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return file_path

def result_file_process(file_path: str):
    # """Reads the Excel file and prepares it for processing."""
    # return pd.read_excel(file_path)
    """
    Process an Excel file and convert each row into a Student object.

    Args:
        input_file (str): Path to the input Excel file.

    Returns:
        list of Student: A list of Student objects.
    """
    # Load the Excel file into a DataFrame
    df = pd.read_excel(file_path)

    students = []

    # Identify the last three columns as ID, Name, and Exam_Code
    id_col = 'F_MASV'
    firstName_col = 'F_HOLOT'
    lastName_col = 'F_TEN'
    exam_code_col = 'MADE'

    # All other columns are considered as answers
    answer_columns = df.columns[:-11]

    # Iterate through each row in the DataFrame
    for _, row in df.iterrows():
        # Extract student information
        student_id = row[id_col]
        firstName = row[firstName_col]
        lastName = row[lastName_col]
        exam_code = row[exam_code_col]

        # Extract answers as a dictionary
        answers = {}
        for col in answer_columns:
            response = row[col]
            if pd.notnull(response):  # Skip if the response is missing
                if response.endswith('1'):
                    answers[col] = {'answer': (ord(response[:-1]) - ord('A')), 'correct': True}
                elif response.endswith('S'):
                    answers[col] = {'answer': (ord(response[:-1]) - ord('A')), 'correct': False}

        # Create a Student object
        student = Student(id=student_id, firstName=firstName, lastName=lastName, exam_code=exam_code, answers=answers)
        students.append(student)

    return students

def process_question_bank(file_path):
    """
    Process a question bank file and populate a QuestionBank object.

    Args:
        file_path (str): Path to the question bank file (Excel or CSV).

    Returns:
        QuestionBank: A QuestionBank object.
    """
    # Load the file into a DataFrame
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please use an Excel or CSV file.")

    # Ensure the file has the required columns
    required_columns = ['Question_ID', 'Content', 'Option_A', 'Option_B', 'Option_C', 'Option_D', 'Correct_Option']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"The file must contain the following columns: {required_columns}")

    # Create a QuestionBank object
    question_bank = QuestionBank()

    # Iterate through the DataFrame and add questions to the QuestionBank
    for _, row in df.iterrows():
        question_id = row['Question_ID']
        content = row['Content']
        options = [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']]
        correct_option = row['Correct_Option']

        # Determine the correct answer index (0-based)
        correct_answer_index = ['A', 'B', 'C', 'D'].index(correct_option)

        # Add the question to the question bank
        question_bank.add_question(question_id, content, options, correct_answer_index)

    return question_bank

file_path = "/Users/thtienn12/Desktop/KQCO2003_DT.xlsx"
students = result_file_process(file_path)
for student in students:
    print(f"ID: {student.id}, lastName: {student.lastName}, Exam Code: {student.exam_code}")
    print(f"Answers: {student.answers}")

