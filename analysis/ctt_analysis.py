import numpy as np

# class Method:
#     examResult = None
#     question_stats = {}

#     def get_number_of_student(self):
#         return 0

#     def get_number_of_questions(self):
#     """
#     Return the total number of questions in the question bank.
#     """
#         return 0

#     def get_average_score(self):
#     """
#     Calculate average scores of all students
#     """
#         scores = [self.examResult.scores[i] for i, student in enumerate(self.examResult.scores)]
#         return scores.mean()

#     def get_average_rbpis(self):
#         None

#     def get_average_difficulty(self):
#         None

#     def get_average_discrimination(self):
#         None


class CttAnalysis:
    examResult = None

    def __init__(self, examResult):
        self.examResult = examResult

    def analyze_questions_ctt(self):
        """
        Main function to analyze questions.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        sorted_students, top_students, bottom_students = self._split_students()

        question_stats = {}
        for question_id, question_data in all_questions.items():
            question_stats[question_id] = self._analyze_single_question(
                question_id,
                question_data,
                sorted_students,
                top_students,
                bottom_students,
            )

        return question_stats

    def _split_students(self):
        """
        Splits students into top and bottom groups based on scores.
        """
        sorted_students = sorted(
            self.examResult.scores, key=lambda x: x["score"], reverse=True
        )

        top_students = [
            s["student"] for s in sorted_students[: len(sorted_students) // 3]
        ]
        bottom_students = [
            s["student"] for s in sorted_students[-len(sorted_students) // 3 :]
        ]
        return sorted_students, top_students, bottom_students

    def _analyze_single_question(
        self, question_id, question_data, sorted_students, top_students, bottom_students
    ):
        """
        Analyzes a single question to compute difficulty and discrimination indices.
        """
        chosen_by, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students
        )
        difficulty_index = chosen_by / len(self.examResult.students)
        discrimination_index = self._compute_discrimination_index(
            question_id, top_students, bottom_students
        )
        difficulty_category = self._categorize_difficulty(difficulty_index)
        discrimination_category = self._categorize_discrimination(discrimination_index)
        all_students = sorted(
            self.examResult.scores, key=lambda x: x["score"], reverse=True
        )
        r_pbis = self._calculate_rpbis(question_id, sorted_students)
        return {
            "difficulty": difficulty_index,
            "difficulty_category": difficulty_category,
            "discrimination": discrimination_index,
            "discrimination_category": discrimination_category,
            "r_pbis": r_pbis,
            "options": option_stats,
        }

    def _compute_option_stats(
        self, question_id, question_data, top_students, bottom_students
    ):
        """
        Computes statistics for each option of a question.
        """
        chosen_by = 0
        total_student = len(self.examResult.students)
        option_stats = {}

        for student in self.examResult.students:
            exam = next(
                (ex for ex in self.examResult.exams if ex.code == student.exam_code),
                None,
            )
            answer_order = exam.answer_order.get(question_id)
            # answer_order = exam.get_answer_order(question_id)
            # print("----------------", student.answers)
            if question_id in student.answers and answer_order is not None:
                correct_answer_index = exam.get_correct_answer(question_id)
                student_answer = student.answers[question_id]["answer"]
                for option in enumerate(answer_order):
                    if student_answer == option[0]:
                        chosen_by = option[1].option_stats.get("chosen_by", 0)
                        # Increment the value
                        chosen_by += 1
                        # Update the dictionary with the new value
                        option[1].option_stats["chosen_by"] = chosen_by
                        option[1].option_stats["selected_by"] += 1
                        option[1].option_stats["ratio"] = chosen_by / total_student
                        if student in top_students:
                            option[1].option_stats["top_selected"] += 1
                        if student in bottom_students:
                            option[1].option_stats["bottom_selected"] += 1
                    option_stats[option[0]] = option[1].option_stats
        return chosen_by, option_stats

    def _compute_discrimination_index(self, question_id, top_students, bottom_students):
        """
        Calculates the discrimination index for a question.
        """
        if len(top_students) == 0 or len(bottom_students) == 0:
            return None

        top_correct = sum(
            1
            for student in top_students
            if self.examResult.is_correct_answer(student, question_id)
        )
        bottom_correct = sum(
            1
            for student in bottom_students
            if self.examResult.is_correct_answer(student, question_id)
        )
        return (top_correct / len(top_students)) - (
            bottom_correct / len(bottom_students)
        )

    def _categorize_difficulty(self, difficulty_index):
        """
        Categorizes difficulty index.
        """
        if difficulty_index >= 0.75:
            return "Very Easy"
        elif difficulty_index >= 0.50:
            return "Easy"
        elif difficulty_index >= 0.25:
            return "Difficult"
        else:
            return "Very Difficult"

    def _categorize_discrimination(self, discrimination_index):
        """
        Categorizes discrimination index.
        """
        if discrimination_index is None:
            return "Unknown"
        elif discrimination_index >= 0.3:
            return "Good"
        elif discrimination_index >= 0.1:
            return "Normal"
        else:
            return "Bad"

    def _calculate_rpbis(self, question_id, all_students):
        """
        Calculates the Rpbis (Relative Position of the Biserial) for a question.

        The Rpbis is a measure of the relative position of the biserial correlation coefficient, which is a measure of the relationship between a question and the total score.

        Args:
            question_id (str): The ID of the question.
            all_students (list): The list of all students.

        Returns:
            float: The Rpbis for the question.
        """
        if len(all_students) == 0:
            return None

        all_scores = [
            self.examResult.scores[i] for i, student in enumerate(all_students)
        ]
        all_scores = [score["score"] for score in all_scores]
        # print("all score ", all_scores)

        correct_students = [
            student
            for student in all_students
            if self.examResult.is_correct_answer(student["student"], question_id)
        ]
        incorrect_students = [
            student
            for student in all_students
            if not self.examResult.is_correct_answer(student["student"], question_id)
        ]
        # for student in incorrect_students:
        #     print(student['score'])

        if len(correct_students) == 0 or len(incorrect_students) == 0:
            return None

        correct_scores = [student["score"] for student in correct_students]
        incorrect_scores = [student["score"] for student in incorrect_students]
        correct_mean = np.mean(correct_scores)
        incorrect_mean = np.mean(incorrect_scores)

        total_std = np.std(all_scores)
        correct_proportion = len(correct_students) / len(all_students)
        incorrect_proportion = 1 - correct_proportion

        rpbis = (
            (correct_mean - incorrect_mean)
            / total_std
            * np.sqrt(correct_proportion * incorrect_proportion)
        )
        return rpbis
