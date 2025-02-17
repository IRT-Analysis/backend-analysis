from analysis.method import Model


class CttAnalysis(Model):
    def analyze_questions_ctt(self):
        """
        Main function to analyze questions.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        total_students = len(self.examResult.students)
        self.general_detail.update(
            {"total_students": total_students, "total_questions": len(all_questions)}
        )

        sorted_students, top_students, bottom_students = self.split_students()

        question_stats_list = [
            self._analyze_single_question(
                question_id,
                question_data,
                sorted_students,
                top_students,
                bottom_students,
            )
            for question_id, question_data in all_questions.items()
        ]

        self.average_indexes.update(
            {
                "average_score": self.get_average_value(
                    "score", self.examResult.scores
                ),
                "average_discrimination": self.get_average_value(
                    "discrimination", question_stats_list
                ),
                "average_difficulty": self.get_average_value(
                    "difficulty", question_stats_list
                ),
                "average_rpbis": self.get_average_value("r_pbis", question_stats_list),
            }
        )

        self.question_stats.update(
            {
                question_id: stat
                for question_id, stat in zip(all_questions.keys(), question_stats_list)
            }
        )

        return self.question_stats

    def _analyze_single_question(
        self, question_id, question_data, sorted_students, top_students, bottom_students
    ):
        """
        Analyzes a single question to compute difficulty and discrimination indices.
        """
        chosen_by, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students, sorted_students
        )

        total_students = len(self.examResult.students)
        difficulty_index = round(chosen_by / total_students, 3)

        discrimination_index = self._compute_discrimination_index(
            question_id, top_students, bottom_students
        )

        difficulty_category = self._categorize_difficulty(difficulty_index)
        discrimination_category = self._categorize_discrimination(discrimination_index)

        r_pbis = self._get_rpbis_of_answer(option_stats, question_id)
        question_bank = self.examResult.exams[0].question_bank

        content = question_bank.get_content(question_id)
        correct_index = question_bank.get_correct_answer_index(question_id)

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

    def _get_rpbis_of_answer(self, option_stats, question_id):
        answer_index = self.examResult.exams[0].question_bank.get_correct_answer_index(
            question_id
        )
        return option_stats[answer_index]["r_pbis"]
