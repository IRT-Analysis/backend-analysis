import pandas as pd
import numpy as np
from typing import Dict, Any, List
from data_structure.student import Student

class DataProcessing:
    def result_file_process(self, file_path: str):
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
                    else: 
                        answers[col] = {'answer': (ord(response[:-1]) - ord('A')), 'correct': None}
                else:
                    answers[col] = {'answer': -1 , 'correct': None}

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

    def process_exam(file_path, question_bank):
        """
        Reads an exam file, matches questions and options to the question bank,
        and processes exams into Exam objects.

        Args:
            file_path (str): Path to the exam file (Excel or CSV).
            question_bank (QuestionBank): The question bank to compare against.

        Returns:
            dict: A dictionary with Exam_code as keys and Exam objects as values.
        """
        # Read the file
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Unsupported file format. Please use an Excel or CSV file.")
        
        # Ensure required columns are present
        required_columns = ['Exam_code', 'Content', 'Option_A', 'Option_B', 'Option_C', 'Option_D', 'Correct_Option']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Group data by Exam_code
        grouped = df.groupby('Exam_code')

        exams = {}

        for exam_code, group in grouped:
            question_order = []
            answer_order = {}

            for _, row in group.iterrows():
                content = row['Content']
                options = [row['Option_A'], row['Option_B'], row['Option_C'], row['Option_D']]
                correct_option = row['Correct_Option']  # Expected to be 'A', 'B', 'C', 'D'

                # Match content with the question bank
                matched_question_id = None
                matched_answer_order = [None] * 4

                for question_id, question_data in question_bank.get_all_questions().items():
                    if question_data['content'] == content:
                        matched_question_id = question_id
                        for idx, option in enumerate(options):
                            if option in question_data['options']:
                                matched_answer_order[idx] = question_data['options'].index(option)
                        break

                if matched_question_id is None:
                    print(f"Warning: Question not found in question bank for Exam Code {exam_code}: {content}")
                    continue

                # Append question order and answer order
                question_order.append(matched_question_id)
                answer_order[matched_question_id] = matched_answer_order

            # Initialize Exam object
            exam = Exam(
                code=exam_code,
                question_bank=question_bank,
                question_order=question_order,
                answer_order=answer_order
            )

            exams[exam_code] = exam

        return exams


# file_path = "/Users/thtienn12/Desktop/KQCO2003_DT.xlsx"
# students = result_file_process(file_path)
# for student in students:
#     print(f"ID: {student.id}, lastName: {student.lastName}, Exam Code: {student.exam_code}")
#     print(f"Answers: {student.answers}")





