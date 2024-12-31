import numpy as np


class CttAnalysis:
    examResult = None
    question_stats = {}
    average_indexes = {}
    general_detail = {}

    def __init__(self, examResult):
        self.examResult = examResult
        self.general_detail = {
            "total_students": 0,
            "total_questions": 0,
            "total_option": 4,
        }

    def _get_average_value(self, name, list):
        temp = [question[name] for question in list]
        if None in temp:
            return 0
        average = np.mean(temp)
        return round(average, 3)

    def analyze_questions_ctt(self):
        """
        Main function to analyze questions.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        self.general_detail["total_students"] = len(self.examResult.students)
        self.general_detail["total_questions"] = len(
            self.examResult.exams[0].question_bank.questions
        )
        sorted_students, top_students, bottom_students = self._split_students()
        list = []
        for question_id, question_data in all_questions.items():
            self.question_stats[question_id] = self._analyze_single_question(
                question_id,
                question_data,
                sorted_students,
                top_students,
                bottom_students,
            )
            list.append(self.question_stats[question_id])

        self.average_indexes["average_score"] = self._get_average_value(
            "score", self.examResult.scores
        )
        self.average_indexes["average_discrimination"] = self._get_average_value(
            "discrimination", list
        )
        self.average_indexes["average_difficulty"] = self._get_average_value(
            "difficulty", list
        )
        self.average_indexes["average_rpbis"] = self._get_average_value("r_pbis", list)
        return self.question_stats

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
        difficulty_index = round(chosen_by / len(self.examResult.students), 3)
        discrimination_index = self._compute_discrimination_index(
            question_id, top_students, bottom_students
        )
        difficulty_category = self._categorize_difficulty(difficulty_index)
        discrimination_category = self._categorize_discrimination(discrimination_index)
        r_pbis = self._calculate_rpbis(question_id, sorted_students)
        content = self.examResult.exams[0].question_bank.get_content(question_id)
        correct_index = self.examResult.exams[0].question_bank.get_correct_answer_index(
            question_id
        )
        group_choice_percentages = self._compute_group_choice_percentages(
            question_id, question_data, sorted_students
        )

        return {
            "content": content,
            "difficulty": difficulty_index,
            "difficulty_category": difficulty_category,
            "discrimination": discrimination_index,
            "discrimination_category": discrimination_category,
            "r_pbis": r_pbis,
            "options": option_stats,
            "correct_index": correct_index,
            "group_choice_percentages": group_choice_percentages,
        }

    def _compute_group_choice_percentages(
        self, question_id, question_data, sorted_students
    ):
        """
        Divides students into 5 groups based on their scores and calculates
        the percentage of choices for the given question in each group.
        """
        # Divide students into 5 groups
        total_students = len(sorted_students)
        group_size = total_students // 5
        student_groups = [
            sorted_students[i * group_size : (i + 1) * group_size]
            for i in reversed(range(5))
        ]

        # Handle leftover students (if total_students is not divisible by 5)
        leftover = total_students % 5
        if leftover > 0:
            student_groups[0].extend(sorted_students[-leftover:])

        # Calculate choice percentages for each group
        group_choice_percentages = []
        for group in student_groups:
            group_choices = {index: 0 for index in range(len(question_data["options"]))}
            # print(group_choices)
            for student in group:
                # Ensure you're accessing the correct level of the nested dictionary
                student_answers = student["student"].answers
                answer_data = student_answers[question_id]
                # print(answer_data)
                if answer_data and "answer" in answer_data:
                    answer = answer_data["answer"]
                    if answer in group_choices:
                        group_choices[answer] += 1
                # print(group_choices)
            # Convert counts to percentages
            group_percentages = {
                option: round(count / len(group), 3) if len(group) > 0 else 0
                for option, count in group_choices.items()
            }
            group_choice_percentages.append(group_percentages)

        return group_choice_percentages

    def _compute_option_stats(
        self, question_id, question_data, top_students, bottom_students
    ):
        """
        Computes statistics for each option of a question.
        """
        chosen_by = 0
        total_student = len(self.examResult.students)
        option_stats = {}
        top_students_len = len(top_students)
        bottom_students_len = len(bottom_students)

        for student in self.examResult.students:
            exam = next(
                (ex for ex in self.examResult.exams if ex.code == student.exam_code),
                None,
            )
            answer_order = exam.answer_order.get(question_id)
            if question_id in student.answers and answer_order is not None:
                correct_answer_index = exam.get_correct_answer(question_id)
                student_answer = student.answers[question_id]["answer"]
                for option in enumerate(answer_order):
                    if student_answer == option[0]:
                        # Increment the value
                        # Update the dictionary with the new value
                        option[1].option_stats["selected_by"] += 1
                        chosen_by = option[1].option_stats["selected_by"]
                        option[1].option_stats["ratio"] = round(
                            option[1].option_stats["selected_by"] / total_student, 3
                        )
                        if student in top_students:
                            option[1].option_stats["top_selected"] += 1
                        if student in bottom_students:
                            option[1].option_stats["bottom_selected"] += 1
                        option[1].option_stats["discrimination"] = round(
                            (
                                option[1].option_stats["top_selected"]
                                / top_students_len
                                - option[1].option_stats["bottom_selected"]
                                / bottom_students_len
                            ),
                            3,
                        )
                        # option[1].students.append(student)
                    option_stats[option[0]] = option[1].option_stats
        return chosen_by, option_stats

    def _calculate_option_rpbis(self, top_student):
        return 0

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
        return round(
            (top_correct / len(top_students)) - (bottom_correct / len(bottom_students)),
            3,
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
        if len(all_students) == 0:
            return None

        all_scores = [
            self.examResult.scores[i] for i, student in enumerate(all_students)
        ]
        all_scores = [score["score"] for score in all_scores]

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
            return 0

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
        if rpbis is None:
            return 0
        return round(rpbis, 3)
