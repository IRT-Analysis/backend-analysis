import asyncio
import os
import uuid
from itertools import groupby
from typing import Dict, List
from openai import AsyncOpenAI
import re
import json

import logging

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

from analysis.ctt_analysis import AverageIndexesType, CttAnalysis, QuestionStatsType
from analysis.irt_analysis import IrtAnalysisType, IrtAnalysis
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
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not self.client:
            raise ValueError("OpenAI API key is not set in the environment variables.")

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

    async def save_analysis_to_supabase(
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
                            "type": "CTT",
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
                "scatter": self.get_scatter_plot(),
            }

            self.handle_insert_histogram(project_id, histogram)

            self.handle_insert_general_detail(
                self.get_general_detail()["total_option"],
                self.get_general_detail()["total_questions"],
                self.get_general_detail()["total_students"],
                project_id,
            )

            # Insert exam
            exam_id = self.handle_insert_exams("Test exam")
            self.handle_insert_exam_analysis(
                exam_id,
                project_id,
                average_indexes["average_difficulty"],
                average_indexes["average_discrimination"],
                0.9,  # Placeholder for Cronbach's alpha, still missing
                average_indexes["average_score"],
                average_indexes["average_rpbis"],
            )

            questions_to_insert = []
            options_to_insert = []
            openai_input = []

            for key, value in analysis_data.items():
                options_data = value["options"]  # a dict like {0: {...}, 1: {...}, ...}

                options = [
                    {
                        "content": value["content"]["option"][i],
                        "ratio": opt["ratio"],
                        "r_pb": opt["r_pbis"],
                        "is_correct": i == value["correct_index"],
                    }
                    for i, opt in options_data.items()
                ]

                openai_input.append(
                    {
                        "question_id": key,
                        "question_text": value["content"]["question"],
                        "difficulty": value["difficulty"],
                        "discrimination": value["discrimination"],
                        "rpbis": value["r_pbis"],
                        "options": options,
                    }
                )

            # Get evaluations
            openai_evaluations = await self.get_question_evaluations_openai(
                openai_input
            )
            question_analysis_to_insert = []
            options_analysis_to_insert = []

            correct_option_mapping = {}

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

                correct_option_mapping[question_id] = correct_index

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
                        "difficulty_index": difficulty,
                        "discrimination_index": discrimination,
                        "rpbis": r_pbis,
                        "group_choice_percentages": group_choice_percentage,
                        "evaluation": openai_evaluations.get(str(key)),  # <-- add this
                    }
                )
                # Step 2: Prepare question analysis

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
                            "selected_by": option_analysis["selected_by"],
                            "top_selected": option_analysis["top_selected"],
                            "bottom_selected": option_analysis["bottom_selected"],
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
            inserted_options = (
                self.supabase.table("options")
                .select("id, question_id")
                .in_("question_id", [q["id"] for q in questions_to_insert])
                .execute()
                .data
            )

            # Build mapping: (question_id, index) → option_id
            question_options_map = {}
            for option in inserted_options:
                question_options_map.setdefault(option["question_id"], []).append(
                    option["id"]
                )

            # Assign correct_option_id back to question
            for q in questions_to_insert:
                qid = q["id"]
                correct_index = correct_option_mapping[qid]
                correct_option_id = question_options_map[qid][correct_index]
                q["correct_option_id"] = correct_option_id

            # Final upsert of questions with correct_option_id
            self.supabase.table("questions").upsert(questions_to_insert).execute()
            student_answers_to_upsert = []
            student_exam_to_insert = []

            for student in student_answer_data:
                student_exam_id = str(uuid.uuid4())
                student_exam_to_insert.append(
                    {
                        "id": student_exam_id,
                        "exam_id": exam_id,
                        "student_id": student["student"].id,
                        "first_name": student["student"].firstName,
                        "last_name": student["student"].lastName,
                        "total_score": student["score"],
                        "grade": (
                            student["score"]
                            / self.analysis.general_detail["total_questions"]
                        ),
                    }
                )
                for question_id, answer in student["student"].answers.items():
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
        exam_data = (
            self.supabase.table("exams")
            .insert([{"code": 1234, "name": name}])
            .execute()
            .data[0]
        )
        return exam_data["id"]

    def handle_insert_exam_analysis(
        self,
        exam_id: str,
        project_id: str,
        avg_difficulty: float,
        avg_discrimination: float,
        cronbach_alpha: float = 0.9,
        average_score: float = 0.42,
        average_rpbis: float = 0.5,
    ):
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
                        "avg_score": average_score,
                        "avg_rpbis": average_rpbis,
                    }
                ]
            )
            .execute()
        )

    def handle_insert_general_detail(
        self, total_options, total_questions, total_students, project_id
    ):
        """
        Insert general detail data into the 'general_detail' table.
        """
        (
            self.supabase.table("projects")
            .update(
                [
                    {
                        "total_options": total_options,
                        "total_questions": total_questions,
                        "total_students": total_students,
                    }
                ]
            )
            .eq("id", project_id)
            .execute()
        )

    def get_score_histogram(self):
        """
        Retrieve the score histogram.
        """

        return self.getData.get_score_list(
            self.exam_result.scores, self.analysis.general_detail["total_questions"]
        )

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

    def get_scatter_plot(self):
        """
        Retrieve the scatter plot data.
        """

        return self.getData.get_scatter_plot_data(self.analysis.question_stats)

    def get_infit_outfit_histogram(self):
        """
        Retrieve the infit values.
        """

        return self.analysis.get_infit_outfit_list(self.analysis.question_stats)

    def get_outfit_histogram(self):
        """
        Retrieve the outfit values.
        """

        return self.getData.get_result_list("outfit", self.analysis.question_stats)

    def get_kr20_index(self):
        """
        Retrieve the KR20 index.
        """

        return self.getData.calculate_kr20(
            self.analysis.question_stats,
            self.analysis.general_detail["total_questions"],
        )

    def handle_insert_histogram(self, project_id: str, data: List[Dict[str, float]]):
        """
        Insert histogram data into the 'histograms' table.
        """
        (
            self.supabase.table("projects")
            .update({"histogram": data})
            .eq("id", project_id)
            .execute()
        )

    async def save_rasch_analysis_to_supabase(
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
                            "type": "Rasch",
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
                "infit_outfit": self.get_infit_outfit_histogram(),
            }

            self.handle_insert_histogram(project_id, histogram)
            self.handle_insert_general_detail(
                4,
                self.get_general_detail()["total_questions"],
                self.get_general_detail()["total_students"],
                project_id,
            )
            # Insert exam
            exam_id = self.handle_insert_exams("Test exam")

            self.supabase.table("exam_analysis").insert(
                [
                    {
                        "exam_id": exam_id,
                        "project_id": project_id,
                        "avg_difficulty_index": average_indexes["average_difficulty"],
                        "avg_discrimination_index": average_indexes[
                            "average_discrimination"
                        ],
                        "cronbach_alpha": 0.9,  # Placeholder for Cronbach's alpha, still missing
                        "avg_score": average_indexes["average_score"],
                        "avg_infit": average_indexes["item_infit"],
                        "avg_outfit": average_indexes["item_outfit"],
                        "avg_reliability": average_indexes["average_reliability"],
                    }
                ]
            ).execute()
            # Create a record in question_analysis table
            questions_to_insert = []
            question_analysis_to_insert = []
            options_to_insert = []
            openai_input = []

            for key, value in analysis_data.items():
                options = value["options"]
                option_list = [
                    {
                        "content": value["content"]["option"][i],
                        "ratio": opt["ratio"],
                        "r_pb": opt["r_pbis"],
                        "is_correct": i == value["correct_index"],
                    }
                    for i, opt in options.items()
                ]

                openai_input.append(
                    {
                        "question_id": key,
                        "question_text": value["content"]["question"],
                        "difficulty": value["difficulty"],
                        "logit": value["logit"],
                        "infit": value["infit"],
                        "outfit": value["outfit"],
                        "reliability": value["reliability"],
                        "options": option_list,
                    }
                )

            evaluations = await self.get_rasch_question_evaluations_openai(openai_input)

            result_analysis_to_insert = []
            options_analysis_to_insert = []

            correct_option_mapping = {}

            # Insert analysis data
            for key, value in analysis_data.items():
                question_content = value["content"]["question"]
                correct_index = value["correct_index"]
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

                correct_option_mapping[question_id] = correct_index

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
                        "evaluation": evaluations.get(str(key)),  # <-- add this
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

            if question_analysis_to_insert:
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
            inserted_options = (
                self.supabase.table("options")
                .select("id, question_id")
                .in_("question_id", [q["id"] for q in questions_to_insert])
                .execute()
                .data
            )
            # Step 4: Update questions with correct_option_ids after options have been inserted

            question_options_map = {}
            for option in inserted_options:
                question_options_map.setdefault(option["question_id"], []).append(
                    option["id"]
                )

            # Assign correct_option_id back to question
            for q in questions_to_insert:
                qid = q["id"]
                correct_index = correct_option_mapping[qid]
                correct_option_id = question_options_map[qid][correct_index]
                q["correct_option_id"] = correct_option_id

            # Final upsert of questions with correct_option_id
            self.supabase.table("questions").upsert(questions_to_insert).execute()

            student_answers_to_upsert = []
            student_exam_to_insert = []

            for student in student_answer_data:
                student_exam_id = str(uuid.uuid4())
                student_exam_to_insert.append(
                    {
                        "id": student_exam_id,
                        "exam_id": exam_id,
                        "student_id": student["student"].id,
                        "first_name": student["student"].firstName,
                        "last_name": student["student"].lastName,
                        "ability": student["student"].ability,
                        "total_score": student["score"],
                        "grade": (
                            student["score"]
                            / self.analysis.general_detail["total_questions"]
                        ),
                    }
                )
                for question_id, answer in student["student"].answers.items():
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

    def build_ctt_prompt(self, questions):
        header = (
            "Bạn là chuyên gia đánh giá chất lượng câu hỏi trắc nghiệm theo mô hình CTT, làm việc cùng giáo viên và nhà nghiên cứu giáo dục. "
            "Mục tiêu là giúp cải thiện ngân hàng câu hỏi bằng cách cung cấp nhận xét có giá trị sư phạm và gợi ý cải tiến khi cần.\n\n"
            "Hãy đánh giá chi tiết từng câu hỏi sau bằng tiếng Việt. Với mỗi câu, viết một đoạn văn hoàn chỉnh theo cấu trúc sau:\n\n"
            "**Mẫu đánh giá chuẩn:**\n"
            "1. **Mở đầu**: Nhận xét tổng quan về độ khó, độ phân biệt, và hệ số tương quan lựa chọn của câu hỏi. Giải thích ý nghĩa nếu chỉ số tốt, trung bình, hoặc có dấu hiệu bất thường.\n"
            "2. **Phân tích phương án lựa chọn**: Nhận xét phương án đúng và các phương án sai có tỷ lệ chọn trên 20% hoặc hệ số tương quan lựa chọn lớn hơn 0.1. "
            "Làm rõ vì sao học sinh có thể chọn sai, mức độ gây nhiễu, và giá trị sư phạm nếu có. Với phương án ít được chọn và không phân biệt tốt thì chỉ cần ghi nhận ngắn gọn.\n"
            "3. **Kết luận**: Đưa ra gợi ý cải tiến nếu câu hỏi có vấn đề về nội dung, độ rõ ràng hoặc thống kê. Nếu hoạt động tốt thì ghi nhận tích cực.\n\n"
            "**Yêu cầu:**\n"
            "- Viết toàn bộ nhận xét thành một đoạn văn duy nhất, rõ ràng, mạch lạc.\n"
            "- Tránh liệt kê hay trình bày theo dạng gạch đầu dòng.\n"
            "- Không sử dụng viết tắt như r_pb, d, discrim,... Thay vào đó hãy viết đầy đủ như “độ khó”, “độ phân biệt”, “hệ số tương quan”.\n"
            "- Không lặp lại thống kê một cách máy móc, cần diễn giải và nhận định có giá trị sư phạm.\n\n"
            "**Định dạng kết quả:** Trả về danh sách JSON. Mỗi phần tử có dạng:\n"
            '{\n  "question_id": string,\n  "evaluation": string\n}\n\n'
            "**Ví dụ:**\n"
            '[\n  {\n    "question_id": "1",\n    "evaluation": "Câu hỏi có độ khó trung bình, hệ số tương quan lựa chọn thấp, cho thấy khả năng phân biệt chưa rõ ràng. '
            'Phương án B là đáp án đúng và được chọn nhiều, tuy nhiên phương án C cũng được chọn khá nhiều và gây nhầm lẫn. Cần điều chỉnh cách diễn đạt phương án sai để tránh gây nhiễu." \n  }\n]\n\n'
            "Chỉ nhận xét các phương án có tỷ lệ chọn > 20% hoặc hệ số tương quan lựa chọn > 0.1.\n\n"
        )

        body = "\n---\n".join(
            [
                f"Câu hỏi:\nID: {q['question_id']}\nNội dung: {q['question_text']}\n"
                f"Thống kê: độ khó = {q['difficulty']}, độ phân biệt = {q['discrimination']}, hệ số tương quan lựa chọn = {q['rpbis']}\n"
                + "\n".join(
                    [
                        f"{chr(65 + i)}. {opt['content']} — tỷ lệ chọn: {opt['ratio']:.1%}, hệ số tương quan lựa chọn: {opt['r_pb']}"
                        + (" (đáp án đúng)" if opt.get("is_correct") else "")
                        for i, opt in enumerate(q["options"])
                        if opt["ratio"] > 0.2
                        or opt["r_pb"] > 0.1
                        or opt.get("is_correct")
                    ]
                )
                for q in questions
            ]
        )

        return header + body

    async def get_question_evaluations_openai(
        self, questions: List[Dict], batch_size: int = 10
    ) -> Dict[str, str]:
        logging.info("Evaluating questions with OpenAI in async batches...")
        batches = self.chunk_questions(questions, batch_size)

        tasks = [
            self.evaluate_batch(
                client=self.client,  # AsyncOpenAI client
                batch=batch,
                build_prompt_fn=self.build_ctt_prompt,  # your prompt builder
                parse_output_fn=self.parse_openai_output,  # your result parser
            )
            for batch in batches
        ]

        results = await asyncio.gather(*tasks)
        all_evaluations = {}
        for result in results:
            all_evaluations.update(result)
        logging.info(f"All evaluations: {all_evaluations}")
        return all_evaluations

    def build_rasch_prompt(self, questions):
        header = (
            "Bạn là chuyên gia đánh giá câu hỏi trắc nghiệm theo mô hình Rasch, làm việc cùng các giáo viên và nhà nghiên cứu giáo dục. "
            "Mục tiêu của bạn là phân tích chất lượng từng câu hỏi để hỗ trợ việc cải tiến ngân hàng đề thi, nâng cao độ tin cậy và giá trị đo lường.\n\n"
            "Hãy đánh giá chi tiết từng câu hỏi sau bằng tiếng Việt. Với mỗi câu, viết một đoạn văn hoàn chỉnh theo cấu trúc sau:\n\n"
            "**Mẫu đánh giá chuẩn:**\n"
            "1. **Mở đầu**: Nhận xét tổng quan về độ khó (difficulty), logit, infit, outfit và độ tin cậy (reliability) của câu hỏi. Giải thích ý nghĩa từng chỉ số nếu có vấn đề. "
            "Nhấn mạnh nếu câu hỏi có chỉ số tốt, trung bình, hay bất thường.\n"
            "2. **Phân tích phương án lựa chọn**: Nhận xét phương án đúng và các phương án sai có tỷ lệ chọn trên 20% hoặc hệ số r_pb > 0.1. "
            "Phân tích lý do học sinh có thể chọn sai, mức độ gây nhiễu, và các dấu hiệu hiểu lầm nếu có. Với các phương án ít được chọn và có r_pb thấp, chỉ cần ghi nhận ngắn gọn.\n"
            "3. **Kết luận**: Nếu chỉ số Rasch hoặc nội dung phương án cho thấy câu hỏi chưa phù hợp, hãy đề xuất cách cải tiến (diễn đạt rõ ràng hơn, loại bỏ phương án nhiễu không hiệu quả, điều chỉnh độ khó...). "
            "Nếu câu hỏi hoạt động tốt thì ghi nhận tích cực.\n\n"
            "**Yêu cầu:**\n"
            "- Viết toàn bộ nội dung thành **một đoạn văn duy nhất, rõ ràng, mạch lạc, phù hợp với giáo viên**.\n"
            "- Không tách thành nhiều mục nhỏ hoặc bullet points trong JSON.\n"
            "- Không viết tắt. Hãy sử dụng từ đầy đủ như “độ khó”, “logit”, “infit”, “outfit”, “độ tin cậy”, “hệ số tương quan lựa chọn”, thay vì d, i, o, r, r_pb...\n"
            "- Không lặp lại thống kê một cách máy móc, mà cần phân tích, giải thích và đưa ra nhận định có ý nghĩa sư phạm.\n\n"
            "**Định dạng kết quả:** Trả về danh sách JSON. Mỗi phần tử có dạng:\n"
            '{\n  "question_id": string,\n  "evaluation": string\n}\n\n'
            "**Ví dụ:**\n"
            '[\n  {\n    "question_id": "1",\n    "evaluation": "Câu hỏi có độ khó trung bình và chỉ số infit/outfit nằm trong mức chấp nhận được, cho thấy mô hình Rasch phù hợp. '
            "Tuy nhiên, phương án C được chọn bởi nhiều học sinh mặc dù sai, chứng tỏ mức độ gây nhiễu cao. Nên xem lại cách diễn đạt phương án đúng để tránh nhầm lẫn. "
            'Câu hỏi có thể được sử dụng nhưng nên theo dõi thêm trong các lần triển khai tiếp theo."\n  }\n]\n\n'
            "Giải thích viết tắt:\n"
            "- d = độ khó (difficulty)\n"
            "- l = logit\n"
            "- i = infit\n"
            "- o = outfit\n"
            "- r = reliability\n"
            "- r_pb = hệ số tương quan lựa chọn\n"
            "- % = tỷ lệ chọn phương án\n\n"
            "Chỉ nhận xét các phương án có tỷ lệ chọn > 20% hoặc r_pb > 0.1.\n\n"
        )

        body = "\n---\n".join(
            [
                f"Câu hỏi:\nID: {q['question_id']}\nNội dung: {q['question_text']}\n"
                f"Thống kê: d={q['difficulty']}, l={q['logit']}, i={q['infit']}, o={q['outfit']}, r={q['reliability']}\n"
                + "\n".join(
                    [
                        f"{chr(65 + i)}. {opt['content']} — {opt['ratio']:.1%}, r_pb={opt['r_pb']}"
                        + (" (đáp án đúng)" if opt.get("is_correct") else "")
                        for i, opt in enumerate(q["options"])
                        if opt["ratio"] > 0.2
                        or opt["r_pb"] > 0.1
                        or opt.get("is_correct")
                    ]
                )
                for q in questions
            ]
        )

        return header + body

    def parse_openai_output(self, raw_output):
        cleaned = re.sub(r"^```json\n|\n```$", "", raw_output.strip())
        return {item["question_id"]: item["evaluation"] for item in json.loads(cleaned)}

    def chunk_questions(self, questions: List[Dict], size: int) -> List[List[Dict]]:
        return [questions[i : i + size] for i in range(0, len(questions), size)]

    async def evaluate_batch(
        self,
        client,
        batch,
        build_prompt_fn,
        parse_output_fn,
        model: str = "gpt-4.1-nano",
    ):
        prompt = build_prompt_fn(batch)
        messages = [
            {
                "role": "system",
                "content": "Bạn là chuyên gia đánh giá câu hỏi trắc nghiệm theo mô hình Rasch, làm việc cùng các giáo viên và nhà nghiên cứu giáo dục. "
                "Mục tiêu của bạn là phân tích chất lượng từng câu hỏi để hỗ trợ việc cải tiến ngân hàng đề thi.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
        try:
            response = await client.responses.create(
                model=model, input=messages, temperature=0.2
            )
            return parse_output_fn(response.output_text)
        except Exception as e:
            logging.error(f"OpenAI evaluation failed for batch: {e}")
            return {}

    # Main method inside your class
    async def get_rasch_question_evaluations_openai(
        self, questions: List[Dict], batch_size: int = 10
    ) -> Dict[str, str]:
        logging.info("Evaluating questions with OpenAI in async batches...")
        batches = self.chunk_questions(questions, batch_size)

        tasks = [
            self.evaluate_batch(
                client=self.client,  # AsyncOpenAI client
                batch=batch,
                build_prompt_fn=self.build_rasch_prompt,  # your prompt builder
                parse_output_fn=self.parse_openai_output,  # your result parser
            )
            for batch in batches
        ]

        results = await asyncio.gather(*tasks)
        all_evaluations = {}
        for result in results:
            all_evaluations.update(result)
        logging.info(f"All evaluations: {all_evaluations}")
        return all_evaluations
