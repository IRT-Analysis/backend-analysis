from itertools import groupby

import pandas as pd

from analysis.ctt_analysis import CttAnalysis
from analysis.method import Method
from models.exam import Exam
from models.exam_result import ExamResult
from models.question import Option, QuestionBank
from utils.data_processing import DataProcessing
from utils.file_handling import save_uploaded_file


class CttService:
    def __init__(self):
        self.analysis = None
        self.getData = None
        self.exam_result = None

    def analyze_uploaded_file(self, result_file, exam_file):
        """
        Process the uploaded file, initialize the exam results, and perform CTT analysis.
        """
        file_path = save_uploaded_file(result_file)
        students = DataProcessing().result_file_process(file_path)
        exam_df = pd.read_csv(exam_file)
        exam_data = exam_df.to_dict(orient="records")
        question_bank = self._load_question_bank(exam_data)

        exams = self._process_exam(exam_data, question_bank)

        self.exam_result = ExamResult(exams, students)
        self.analysis = CttAnalysis(self.exam_result)
        print("analyze_uploaded_file")
        self.getData = Method()
        self.analysis.analyze_questions_ctt()

    def get_analysis_results(self):
        """
        Retrieve the analysis results.
        """
        if self.analysis:
            return self.analysis.question_stats
        raise ValueError("CTT analysis not initialized.")

    def get_general_detail(self):
        """
        Retrieve general details from the CTT analysis.
        """
        if self.analysis:
            return self.analysis.general_detail
        raise ValueError("CTT analysis not initialized.")

    def get_question_stats(self, question_id):
        """
        Retrieve stats for a specific question.
        """
        if not self.analysis:
            raise ValueError("CTT analysis not initialized.")

        sorted_students, top_students, bottom_students = self.analysis.split_students()
        all_questions = self.analysis.examResult.exams[
            0
        ].question_bank.get_all_questions()
        question_data = all_questions.get(question_id)

        if not question_data:
            raise ValueError(f"Question with ID {question_id} not found.")

        return self.analysis._analyze_single_question(
            question_id, question_data, sorted_students, top_students, bottom_students
        )

    def get_average_indexes(self):
        """
        Retrieve average indexes (difficulty, discrimination, etc.).
        """
        if self.analysis:
            return self.analysis.average_indexes
        raise ValueError("CTT analysis not initialized.")

    def _load_question_bank(self, exam_data):
        """
        Load question bank data from a predefined file.
        """
        question_bank = QuestionBank()
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
        return question_bank

    def _process_exam(self, exam_data, question_bank):
        """
        Process exam data and group by Exam Code.
        """
        exam_data.sort(key=lambda x: x["Exam_code"])
        grouped = {
            key: list(group)
            for key, group in groupby(exam_data, key=lambda x: x["Exam_code"])
        }

        exams = []
        for exam_code, group in grouped.items():
            question_order = []
            answer_order = {}

            for question in group:
                matched_question = next(
                    (
                        q_id
                        for q_id, q_data in question_bank.get_all_questions().items()
                        if q_data["content"] == question["Content"]
                    ),
                    None,
                )
                if not matched_question:
                    print(
                        f"Warning: Question not found for Exam Code {exam_code}: {question['Content']}"
                    )
                    continue
                question_order.append(matched_question)
                answer_order[matched_question] = question_bank.get_all_questions()[
                    matched_question
                ]["options"]

            exams.append(Exam(exam_code, question_bank, question_order, answer_order))

        return exams

    def get_score_histogram(self):
        """
        Retrieve the score histogram.
        """

        return self.getData.get_score_list(self.exam_result.scores)

    def get_discrimination_histogram(self):
        """
        Retrieve the discrimination values.
        """

        return self.getData.get_result_list(
            "discrimination", self.analysis.question_stats
        )

    def get_difficultiy_histogram(self):
        """
        Retrieve the discrimination values.
        """

        return self.getData.get_result_list("difficulty", self.analysis.question_stats)

    def get_rpbis_histogram(self):
        """
        Retrieve the discrimination values.
        """

        return self.getData.get_result_list("r_pbis", self.analysis.question_stats)
