import pandas as pd
from models.question import QuestionBank
from models.student import Student
from models.exam import Exam

class DataProcessing:
    def result_file_process(self, file_path: str):
        """
        Process an Excel file and convert each row into a Student object.

        Args:
            file_path (str): Path to the input Excel file.

        Returns:
            list of Student: A list of Student objects.

        Raises:
            ValueError: If the file is invalid or missing required columns.
        """

        # 1. Check if the file is an Excel file (invalid file type handling)
        if not file_path.endswith((".xlsx", ".xls")):
            raise ValueError(
                "Invalid file type. Expected an Excel file (.xlsx or .xls)."
            )

        # 2. Attempt to load the Excel file into a DataFrame
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read the Excel file: {e}")

        # 3. Validate required columns (invalid content handling)
        required_columns = ["F_MASV", "F_HOLOT", "F_TEN", "MADE"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {', '.join(missing_columns)} in {file_path}"
            )

        # Process the file if it passes all validations
        students = []

        # All other columns are considered as answers
        answer_columns = df.columns[:-11]

        # Iterate through each row in the DataFrame
        for _, row in df.iterrows():
            # Extract student information
            student_id = row["F_MASV"]
            firstName = row["F_HOLOT"]
            lastName = row["F_TEN"]
            exam_code = row["MADE"]

            # Extract answers as a dictionary
            answers = {}
            for colOrder in answer_columns:
                col = colOrder[1:]
                col = int(col)
                response = row[colOrder]
                if pd.notnull(response):  # Skip if the response is missing
                    if response.endswith("1"):
                        answers[col] = {
                            "answer": (ord(response[:-1]) - ord("A")),
                            "correct": True,
                        }
                    elif response.endswith("S"):
                        # Edge case where the response is "*S"
                        if response.startswith("*"):
                            answers[col] = {"answer": -1, "correct": None}
                        else:
                            answers[col] = {
                                "answer": (ord(response[:-1]) - ord("A")),
                                "correct": False,
                            }
                    else:
                        answers[col] = {
                            "answer": (ord(response[:-1]) - ord("A")),
                            "correct": None,
                        }
                else:
                    answers[col] = {"answer": -1, "correct": None}

            # Create a Student object
            student = Student(
                id=student_id,
                firstName=firstName,
                lastName=lastName,
                exam_code=exam_code,
                answers=answers,
            )
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
        if file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        elif file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            raise ValueError(
                "Unsupported file format. Please use an Excel or CSV file."
            )

        # Ensure the file has the required columns
        required_columns = [
            "Exam_code",
            "Content",
            "Option_A",
            "Option_B",
            "Option_C",
            "Option_D",
            "Correct_Option",
        ]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(
                f"The file must contain the following columns: {required_columns}"
            )

        # Create a QuestionBank object
        question_bank = QuestionBank()
        question_id = 0
        exam_code = df[1]["Exam_code"]
        # Iterate through the DataFrame and add questions to the QuestionBank
        for _, row in df.iterrows():
            if row["Exam_code"] == exam_code:
                question_id = question_id + 1
                content = row["Content"]
                options = [
                    row["Option_A"],
                    row["Option_B"],
                    row["Option_C"],
                    row["Option_D"],
                ]
                correct_option = row["Correct_Option"]

                # Determine the correct answer index (0-based)
                correct_answer_index = ["A", "B", "C", "D"].index(correct_option)

                # Add the question to the question bank
                question_bank.add_question(
                    question_id, content, options, correct_answer_index
                )
            else:
                break

        return question_bank

def process_exam(file_path, question_bank):
    # Load the file into a DataFrame
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please use an Excel or CSV file.")

    # Group data by Exam_code
    # file_path.sort(key=lambda x: x['Exam_code'])
    # Ensure required columns are present
    required_columns = [
        "Exam_code",
        "Content",
        "Option_A",
        "Option_B",
        "Option_C",
        "Option_D",
        "Correct_Option",
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Group data by Exam_code
    grouped = df.groupby("Exam_code")

    # Group the data by 'Exam_code'
    # grouped = {key: list(file_path) for key, group in groupby(file_path, key=lambda x: x['Exam_code'])}

    exams = []

    for exam_code, group in grouped:
        question_order = []
        answer_order = {}

        for _, question in group.iterrows():
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

