from data_structure.question import QuestionBank 
from data_structure.exam import Exam
from data_structure.student import Student
from data_structure.examResult import ExamResult
from data_structure.option import Option
from method.ctt_analysis import CttAnalysis
from data_processing import DataProcessing 

from itertools import groupby
# Tạo bộ câu hỏi chuẩn
question_bank = QuestionBank()

question_bank_data = [
    {"Question_ID": "Q001", "Content": "What is the capital of France?", "Option_A": "London", "Option_B": "Paris", "Option_C": "Berlin", "Option_D": "Rome", "Correct_Option": "B"},
    {"Question_ID": "Q002", "Content": "What is 2+2?", "Option_A": "4", "Option_B": "5", "Option_C": "6", "Option_D": "3", "Correct_Option": "A"},
    {"Question_ID": "Q003", "Content": "What is 3+5?", "Option_A": "7", "Option_B": "8", "Option_C": "9", "Option_D": "10", "Correct_Option": "B"},
    {"Question_ID": "Q004", "Content": "What is the largest ocean?", "Option_A": "Atlantic", "Option_B": "Indian", "Option_C": "Arctic", "Option_D": "Pacific", "Correct_Option": "D"},
    {"Question_ID": "Q005", "Content": "Who wrote '1984'?", "Option_A": "George Orwell", "Option_B": "J.K. Rowling", "Option_C": "Mark Twain", "Option_D": "Hemingway", "Correct_Option": "A"},
    {"Question_ID": "Q006", "Content": "What is the chemical symbol for water?", "Option_A": "H2O", "Option_B": "O2", "Option_C": "CO2", "Option_D": "H2", "Correct_Option": "A"},
    {"Question_ID": "Q007", "Content": "Which planet is known as the Red Planet?", "Option_A": "Venus", "Option_B": "Earth", "Option_C": "Mars", "Option_D": "Jupiter", "Correct_Option": "C"},
    {"Question_ID": "Q008", "Content": "What is the square root of 16?", "Option_A": "2", "Option_B": "4", "Option_C": "8", "Option_D": "16", "Correct_Option": "B"},
    {"Question_ID": "Q009", "Content": "Who is the first President of the United States?", "Option_A": "Abraham Lincoln", "Option_B": "George Washington", "Option_C": "Thomas Jefferson", "Option_D": "John Adams", "Correct_Option": "B"},
    {"Question_ID": "Q010", "Content": "What is the capital of Japan?", "Option_A": "Seoul", "Option_B": "Beijing", "Option_C": "Tokyo", "Option_D": "Kyoto", "Correct_Option": "C"},
    {"Question_ID": "Q011", "Content": "Which element has the atomic number 1?", "Option_A": "Helium", "Option_B": "Hydrogen", "Option_C": "Oxygen", "Option_D": "Carbon", "Correct_Option": "B"},
    {"Question_ID": "Q012", "Content": "Who painted the Mona Lisa?", "Option_A": "Vincent van Gogh", "Option_B": "Pablo Picasso", "Option_C": "Leonardo da Vinci", "Option_D": "Claude Monet", "Correct_Option": "C"},
    {"Question_ID": "Q013", "Content": "What is the largest continent?", "Option_A": "Africa", "Option_B": "Asia", "Option_C": "Europe", "Option_D": "North America", "Correct_Option": "B"},
    {"Question_ID": "Q014", "Content": "Which country is known as the Land of the Rising Sun?", "Option_A": "China", "Option_B": "Japan", "Option_C": "South Korea", "Option_D": "India", "Correct_Option": "B"},
    {"Question_ID": "Q015", "Content": "What is the boiling point of water in Celsius?", "Option_A": "50°C", "Option_B": "100°C", "Option_C": "150°C", "Option_D": "200°C", "Correct_Option": "B"},
    {"Question_ID": "Q016", "Content": "What is the largest animal on Earth?", "Option_A": "Elephant", "Option_B": "Blue whale", "Option_C": "Giraffe", "Option_D": "Shark", "Correct_Option": "B"},
    {"Question_ID": "Q017", "Content": "Which element is diamond made of?", "Option_A": "Gold", "Option_B": "Oxygen", "Option_C": "Carbon", "Option_D": "Nitrogen", "Correct_Option": "C"},
    {"Question_ID": "Q018", "Content": "What is the currency of the United Kingdom?", "Option_A": "Euro", "Option_B": "Pound", "Option_C": "Dollar", "Option_D": "Yen", "Correct_Option": "B"},
    {"Question_ID": "Q019", "Content": "Which gas do plants absorb from the atmosphere?", "Option_A": "Oxygen", "Option_B": "Hydrogen", "Option_C": "Carbon Dioxide", "Option_D": "Nitrogen", "Correct_Option": "C"},
    {"Question_ID": "Q020", "Content": "What is the freezing point of water?", "Option_A": "-10°C", "Option_B": "0°C", "Option_C": "10°C", "Option_D": "32°C", "Correct_Option": "B"}
]

for question in question_bank_data:
    question_id = question['Question_ID']
    question_content = question['Content']
    # options = [question['Option_A'], question['Option_B'], question['Option_C'], question['Option_D']]
    options = [Option(question['Option_A']), Option(question['Option_B']), Option(question['Option_C']), Option(question['Option_D'])]
    correct_answer = question['Correct_Option']
    correct_answer_index = ['A', 'B', 'C', 'D'].index(correct_answer)
    
    # Add the question to the QuestionBank
    question_bank.add_question(question_id, question_content, options, correct_answer_index)

# # Now the question bank contains the questions
# print(question_bank.get_all_questions())
student_results_data = [
    {"Student_ID": "S001", "First_Name": "John", "Last_Name": "Doe", "Exam_code": "EX001", "Q001": "B1", "Q002": "A1", "Q003": "BS", "Q004": "DS"},
    {"Student_ID": "S002", "First_Name": "Jane", "Last_Name": "Smith", "Exam_code": "EX001", "Q1": "AS", "Q2": "B1", "Q3": "C1", "Q4": "DS"},
    {"Student_ID": "S003", "First_Name": "Bob", "Last_Name": "Lee", "Exam_code": "EX002", "Q1": "A1", "Q2": "B1", "Q3": "C1", "Q4": "D1"},
    {"Student_ID": "S004", "First_Name": "Emily", "Last_Name": "White", "Exam_code": "EX002", "Q1": "AS", "Q2": "B1", "Q3": "C1", "Q4": "DS"},
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
            if key.startswith('Q'):  # Only process the questions (Q1, Q2, etc.)
                question_id = key  # e.g., 'Q1'
                
                # Determine the answer and correctness
                answer_value = value[:-1]  # Get the answer part (A, B, C, etc.)
                is_correct = False
                if value.endswith('1'):
                    is_correct = True
                elif value.endswith('S'):
                    is_correct = False
                elif value == "":  # For unanswered questions
                    is_correct = None
                
                # Convert the answer letter to an index (0 for A, 1 for B, etc.)
                option_index = ['A', 'B', 'C', 'D'].index(answer_value)
                # Store answer in the dictionary with the new structure
                answers[question_id] = {
                    'answer': option_index,  # Answer as index list (can be extended if needed)
                    'correct': is_correct
                }
        
        # Create a Student object
        student = Student(student_id, first_name, last_name, exam_code, answers)
        students.append(student)
    
    return students

# Process the student results and create Student objects
students = process_student_results(student_results_data, question_bank_data)
# for student in students:
#     print(f"ID: {student.id}, Name: {student.firstName} {student.lastName}, Exam Code: {student.exam_code}, Answers: {student.answers}")

def process_exam(file_path, question_bank):
    # Group data by Exam_code
    file_path.sort(key=lambda x: x['Exam_code'])

    # Group the data by 'Exam_code'
    grouped = {key: list(file_path) for key, group in groupby(file_path, key=lambda x: x['Exam_code'])}

    exams = []

    for exam_code, group in grouped.items():
        question_order = []
        answer_order ={}

        for question in group:
            content = question['Content']
            options = [question['Option_A'], question['Option_B'], question['Option_C'], question['Option_D']]
            correct_option = question['Correct_Option']

            # Match content with the question bank
            matched_question_id = None
            matched_answer_order = [None] * 4

            for question_id, question_data in question_bank.get_all_questions().items():
                if question_data['content'] == content:
                    matched_question_id = question_id
                    matched_answer_order = question_data['options']
                    # for idx, option in enumerate(options):
                    #     # if option in question_data['options']:
                    #     matched_answer_order[idx] = question_data['options'].index(option)
                    # break

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

        exams.append(exam) 

    return exams

exam_file_data = [
    {"Exam_code": "EX001", "Content": "What is the capital of France?", "Option_A": "London", "Option_B": "Paris", "Option_C": "Berlin", "Option_D": "Rome", "Correct_Option": "B"},
    {"Exam_code": "EX001", "Content": "What is 2+2?", "Option_A": "4", "Option_B": "5", "Option_C": "6", "Option_D": "3", "Correct_Option": "A"},
    {"Exam_code": "EX002", "Content": "What is 3+5?", "Option_A": "7", "Option_B": "8", "Option_C": "9", "Option_D": "10", "Correct_Option": "B"},
    {"Exam_code": "EX002", "Content": "What is the largest ocean?", "Option_A": "Atlantic", "Option_B": "Indian", "Option_C": "Arctic", "Option_D": "Pacific", "Correct_Option": "D"},
    {"Exam_code": "EX002", "Content": "What is 2+2?", "Option_A": "4", "Option_B": "5", "Option_C": "6", "Option_D": "3", "Correct_Option": "A"},
    {"Exam_code": "EX002", "Content": "What is the capital of France?", "Option_A": "London", "Option_B": "Paris", "Option_C": "Berlin", "Option_D": "Rome", "Correct_Option": "B"},
]

exams = process_exam(exam_file_data, question_bank)
examResult = ExamResult(exams, students)
analysis = CttAnalysis(examResult)
print(analysis.analyze_questions_ctt())

