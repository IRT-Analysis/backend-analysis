import logging
import os
from turtle import mode
import uuid
from itertools import groupby
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

from analysis.ctt_analysis import AverageIndexesType, CttAnalysis, QuestionStatsType
from analysis.irt_analysis import IrtAnalysisType
from analysis.irt_analysis import IrtAnalysis
from analysis.method import Method
from models.exam import Exam
from models.exam_result import ExamResult
from models.question import Option, QuestionBank
from models.student import StudentDictType
from utils.data_processing import DataProcessing
from utils.file_handling import save_uploaded_file

load_dotenv()


class AnalysisService:
    def __init__(self):
        self.analysis = None
        self.getData = None
        self.exam_result = None
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
        )

    def analyze_uploaded_file(
        self,
        result_file,
        exam_file,
        analysis_method="CTT",
    ):
        # Save the uploaded file, might be removed in the future, as the file is read directly
        file_path = save_uploaded_file(result_file)
        # List of students info and their answers
        students = DataProcessing().result_file_process(file_path)
        exam_df = pd.read_csv(exam_file)
        exam_data = exam_df.to_dict(orient="records")

        # This one is for processing the exam data (questions and options)
        # returns a dictionary of questions
        question_bank = self._load_question_bank(exam_data)

        # Group the exam data by Exam Code
        exams = self._process_exam(exam_data, question_bank)

        self.exam_result = ExamResult(exams, students)

        # analysis_methods = {
        #     "CTT": CttAnalysis,
        #     "IRT": IrtAnalysis,
        #     # "Rasch": RaschAnalysis,
        # }
        analysis_methods = {
            "CTT": CttAnalysis,
            "Rasch": IrtAnalysis,
            # "Rasch": RaschAnalysis,
        }

        if analysis_method not in analysis_methods:
            raise ValueError(f"Unsupported analysis method: {analysis_method}")

        # Perform the chosen analysis
        # self.analysis = analysis_methods[analysis_method](self.exam_result)
        # self.analysis.analyze_questions()
        if analysis_method == "CTT":
            self.analysis = CttAnalysis(self.exam_result)
            self.analysis.analyze_questions()
        elif analysis_method == "Rasch":
            model = IrtAnalysis(self.exam_result)
            model.rasch_analysis()
            self.analysis = model
        self.getData = Method()

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

    def get_student_answer(self) -> List[StudentDictType]:
        """
        Retrieve the student answer.
        """
        return self.exam_result.to_dict().get("students")

    def save_analysis_to_supabase(
        self,
        project_name,
        number_of_group,
        group_percentage,
        correlation_rpbis,
        analysis_data: Dict[str, QuestionStatsType],
        student_answer_data: List[StudentDictType],
        average_indexes: AverageIndexesType,
        user_id: str,
    ):
        """
        Save analysis data and student answers to Supabase.
        """
        try:
            # Insert project
            project_data = (
                self.supabase.table("projects")
                .insert(
                    [
                        {
                            "user_id": user_id,
                            "name": project_name,
                            "description": "TBD",
                        }
                    ]
                )
                .execute()
                .data[0]
            )
            project_id = project_data["id"]

            histogram = {
                "score": self.get_score_histogram(),
                "discrimination": self.get_discrimination_histogram(),
                "difficulty": self.get_difficultiy_histogram(),
                "r_pbis": self.get_rpbis_histogram(),
            }

            self.handle_insert_histogram(project_id, histogram)

            # Insert exam
            exam_id = self.handle_insert_exams("Test exam")
            self.handle_insert_exam_analysis(
                exam_id,
                project_id,
                average_indexes["average_difficulty"],
                average_indexes["average_discrimination"],
            )

            questions_to_insert = []
            options_to_insert = []
            question_analysis_to_insert = []
            options_analysis_to_insert = []

            # Insert analysis data
            for key, value in analysis_data.items():
                question_content = value["content"]["question"]
                correct_index = value["correct_index"]
                difficulty = value["difficulty"]
                discrimination = value["discrimination"]
                r_pbis = value["r_pbis"]
                options = value["options"]
                group_choice_percentage = value["group_choice_percentages"]

                # Step 1: Create question with a temporary correct_option_id (initially None)
                question_id = str(uuid.uuid4())
                value["question_id"] = question_id
                questions_to_insert.append(
                    {
                        "id": question_id,
                        "exam_id": exam_id,
                        "content": question_content,
                        "correct_option_id": None,  # Placeholder for later update
                    }
                )

                # Step 2: Prepare question analysis
                question_analysis_to_insert.append(
                    {
                        "exam_id": exam_id,
                        "question_id": question_id,
                        "difficulty_index": difficulty,
                        "discrimination_index": discrimination,
                        "rpbis": r_pbis,
                        "group_choice_percentages": group_choice_percentage,
                    }
                )

                # Step 3: Create options and their analysis
                for index, option_content in enumerate(value["content"]["option"]):
                    option_id = str(uuid.uuid4())
                    options_to_insert.append(
                        {
                            "id": option_id,
                            "question_id": question_id,  # Link to the question
                            "content": option_content,
                        }
                    )

                    option_analysis = options[index]
                    option_analysis["option_id"] = option_id
                    options_analysis_to_insert.append(
                        {
                            "option_id": option_id,
                            "exam_id": exam_id,
                            "discrimination_index": option_analysis["discrimination"],
                            "rpbis": option_analysis["r_pbis"],
                            "selection_rate": option_analysis["ratio"],
                        }
                    )

            # Perform bulk inserts for questions
            if questions_to_insert:
                self.supabase.table("questions").insert(questions_to_insert).execute()

            # Perform bulk inserts for question analysis
            if question_analysis_to_insert:
                self.supabase.table("question_analysis").insert(
                    question_analysis_to_insert
                ).execute()

            # Perform bulk inserts for options
            if options_to_insert:
                self.supabase.table("options").insert(options_to_insert).execute()

            # Perform bulk inserts for options analysis
            if options_analysis_to_insert:
                self.supabase.table("option_analysis").insert(
                    options_analysis_to_insert
                ).execute()

            # Step 4: Update questions with correct_option_ids after options have been inserted
            for i, question in enumerate(questions_to_insert):
                correct_index = analysis_data[key][
                    "correct_index"
                ]  # Get correct index from original data
                correct_option_id = options_to_insert[
                    correct_index
                    + sum(
                        len(value["content"]["option"])
                        for value in analysis_data.values()
                        if value["content"]["question"] != question["content"]
                    )
                ]["id"]

                # Update the correct_option_id in the questions list
                questions_to_insert[i]["correct_option_id"] = correct_option_id
            self.supabase.table("questions").upsert(questions_to_insert).execute()

            student_answers_to_upsert = []
            student_exam_to_insert = []

            for student in student_answer_data:
                student_exam_id = str(uuid.uuid4())
                student_exam_to_insert.append(
                    {
                        "id": student_exam_id,
                        "exam_id": exam_id,
                        "student_id": student["id"],
                        "first_name": student["firstName"],
                        "last_name": student["lastName"],
                    }
                )
                for question_id, answer in student["answers"].items():
                    logging.info(
                        f"Inserting/updating answer for question ID: {question_id}"
                    )

                    option_id = None
                    if answer["answer"] != -1:
                        option_id = analysis_data[question_id]["options"][
                            answer["answer"]
                        ]["option_id"]

                    is_correct = (
                        answer.get("correct")
                        if answer.get("correct") is not None
                        else False
                    )

                    student_answers_to_upsert.append(
                        {
                            "student_exam_id": student_exam_id,
                            "question_id": analysis_data[question_id][
                                "question_id"
                            ],  # Assuming this is the ID used in your DB
                            "selected_option_id": option_id,
                            "selected_option_index": answer["answer"],
                            "is_correct": is_correct,
                        }
                    )

            if student_exam_to_insert:
                self.supabase.table("student_exams").insert(
                    student_exam_to_insert
                ).execute()

            if student_answers_to_upsert:
                self.supabase.table("student_answers").upsert(
                    student_answers_to_upsert,
                ).execute()

            return {
                "message": "File uploaded and data saved successfully.",
                "data": {"projectId": project_id, "examId": [exam_id]},
                "code": 201,
            }

        except Exception as e:
            raise ValueError(f"Error saving data to Supabase: {str(e)}")

    def handle_insert_exams(self, name):
        """
        Insert exam data into the 'exams' table.
        """
        logging.info("Inserting exam data")
        exam_data = (
            self.supabase.table("exams")
            .insert([{"code": 1234, "name": name}])
            .execute()
            .data[0]
        )
        # logging.info(exam_data["id"])
        return exam_data["id"]

    def handle_insert_exam_analysis(
        self,
        exam_id: str,
        project_id: str,
        avg_difficulty: float,
        avg_discrimination: float,
        cronbach_alpha: float = 0.5,
    ):
        logging.info("Inserting exam analysis data")
        logging.info(
            exam_id, project_id, avg_difficulty, avg_discrimination, cronbach_alpha
        )
        (
            self.supabase.table("exam_analysis")
            .insert(
                [
                    {
                        "exam_id": exam_id,
                        "project_id": project_id,
                        "avg_difficulty_index": avg_difficulty,
                        "avg_discrimination_index": avg_discrimination,
                        "cronbach_alpha": cronbach_alpha,
                    }
                ]
            )
            .execute()
        )

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

    def handle_insert_histogram(self, project_id: str, data: List[Dict[str, float]]):
        """
        Insert histogram data into the 'histograms' table.
        """
        logging.info("Inserting histogram data")
        (
            self.supabase.table("projects")
            .update({"histogram": data})
            .eq("id", project_id)
            .execute()
        )

    def save_rasch_analysis_to_supabase(
        self,
        project_name,
        number_of_group,
        group_percentage,
        correlation_rpbis,
        analysis_data: Dict[str, IrtAnalysisType],
        student_answer_data: List[StudentDictType],
        average_indexes: AverageIndexesType,
        user_id: str,
    ):
        """
        Save analysis data and student answers to Supabase.
        """
        try:
            # Insert project
            project_data = (
                self.supabase.table("projects")
                .insert(
                    [
                        {
                            "user_id": user_id,
                            "name": project_name,
                            "description": "TBD",
                        }
                    ]
                )
                .execute()
                .data[0]
            )
            project_id = project_data["id"]

            histogram = {
                "score": self.get_score_histogram(),
                "discrimination": self.get_discrimination_histogram(),
                "difficulty": self.get_difficultiy_histogram(),
                # "r_pbis": self.get_rpbis_histogram(),
            }

            self.handle_insert_histogram(project_id, histogram)

            # Insert exam
            exam_id = self.handle_insert_exams("Test exam")

            self.handle_insert_exam_analysis(
                exam_id,
                project_id,
                average_indexes["average_difficulty"],
                average_indexes["average_discrimination"],
            )

            # Create a record in question_analysis table
            question_analysis_id = str(uuid.uuid4())

            questions_to_insert = []
            question_analysis_to_insert = []
            options_to_insert = []
            result_analysis_to_insert = []
            options_analysis_to_insert = []

            # Insert analysis data
            for key, value in analysis_data.items():
                question_content = value["content"]["question"]
                difficulty = value["difficulty"]
                discrimination = value["discrimination"]
                logit = value["logit"]
                infit = value["infit"]
                outfit = value["outfit"]
                reliability = value["reliability"]
                options = value["options"]

                # Step 1: Create question with a temporary correct_option_id (initially None)
                question_id = str(uuid.uuid4())
                value["question_id"] = question_id
                questions_to_insert.append(
                    {
                        "id": question_id,
                        "exam_id": exam_id,
                        "content": question_content,
                        "correct_option_id": None,  # Placeholder for later update
                    }
                )
                question_analysis_id = str(uuid.uuid4())
                question_analysis_to_insert.append(
                    {
                        "id": question_analysis_id,
                        "question_id": question_id,
                        "exam_id": exam_id,
                    }
                )

                # Step 2: Prepare question analysis
                result_analysis_to_insert.append(
                    {
                        "question_analysis_id": question_analysis_id,
                        "difficulty": difficulty,
                        "discrimination": discrimination,
                        "logit": logit,
                        "infit": infit,
                        "outfit": outfit,
                        "reliability": reliability,
                    }
                )

                # Step 3: Create options and their analysis
                for index, option_content in enumerate(value["content"]["option"]):
                    option_id = str(uuid.uuid4())
                    options_to_insert.append(
                        {
                            "id": option_id,
                            "question_id": question_id,  # Link to the question
                            "content": option_content,
                        }
                    )

                    option_analysis = options[index]
                    option_analysis["option_id"] = option_id
                    options_analysis_to_insert.append(
                        {
                            "option_id": option_id,
                            "exam_id": exam_id,
                            "discrimination_index": option_analysis["discrimination"],
                            "rpbis": option_analysis["r_pbis"],
                            "selection_rate": option_analysis["ratio"],
                            "top_selected": option_analysis["top_selected"],
                            "bottom_selected": option_analysis["bottom_selected"],
                        }
                    )

            # Perform bulk inserts for questions
            if questions_to_insert:
                self.supabase.table("questions").insert(questions_to_insert).execute()

            self.supabase.table("question_analysis").insert(
                question_analysis_to_insert
            ).execute()

            # Perform bulk inserts for question analysis
            if result_analysis_to_insert:
                self.supabase.table("rasch_analysis").insert(
                    result_analysis_to_insert
                ).execute()

            # Perform bulk inserts for options
            if options_to_insert:
                self.supabase.table("options").insert(options_to_insert).execute()

            # Perform bulk inserts for options analysis
            if options_analysis_to_insert:
                self.supabase.table("option_analysis").insert(
                    options_analysis_to_insert
                ).execute()

            # Step 4: Update questions with correct_option_ids after options have been inserted
            for i, question in enumerate(questions_to_insert):
                correct_index = analysis_data[key][
                    "correct_index"
                ]  # Get correct index from original data
                correct_option_id = options_to_insert[
                    correct_index
                    + sum(
                        len(value["content"]["option"])
                        for value in analysis_data.values()
                        if value["content"]["question"] != question["content"]
                    )
                ]["id"]

                # Update the correct_option_id in the questions list
                questions_to_insert[i]["correct_option_id"] = correct_option_id
            self.supabase.table("questions").upsert(questions_to_insert).execute()

            student_answers_to_upsert = []
            student_exam_to_insert = []

            for student in student_answer_data:
                student_exam_id = str(uuid.uuid4())
                student_exam_to_insert.append(
                    {
                        "id": student_exam_id,
                        "exam_id": exam_id,
                        "student_id": student["id"],
                        "first_name": student["firstName"],
                        "last_name": student["lastName"],
                    }
                )
                for question_id, answer in student["answers"].items():
                    logging.info(
                        f"Inserting/updating answer for question ID: {question_id}"
                    )

                    option_id = None
                    if answer["answer"] != -1:
                        option_id = analysis_data[question_id]["options"][
                            answer["answer"]
                        ]["option_id"]

                    is_correct = (
                        answer.get("correct")
                        if answer.get("correct") is not None
                        else False
                    )

                    student_answers_to_upsert.append(
                        {
                            "student_exam_id": student_exam_id,
                            "question_id": analysis_data[question_id][
                                "question_id"
                            ],  # Assuming this is the ID used in your DB
                            "selected_option_id": option_id,
                            "selected_option_index": answer["answer"],
                            "is_correct": is_correct,
                        }
                    )

            if student_exam_to_insert:
                self.supabase.table("student_exams").insert(
                    student_exam_to_insert
                ).execute()

            if student_answers_to_upsert:
                self.supabase.table("student_answers").upsert(
                    student_answers_to_upsert,
                ).execute()

            return {
                "message": "File uploaded and data saved successfully.",
                "data": {"projectId": project_id, "examId": [exam_id]},
                "code": 201,
            }

        except Exception as e:
            raise ValueError(f"Error saving data to Supabase: {str(e)}")
