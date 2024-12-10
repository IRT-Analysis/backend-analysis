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
                question_id, question_data, top_students, bottom_students
            )

        return question_stats

    def _split_students(self):
        """
        Splits students into top and bottom groups based on scores.
        """
        sorted_students = sorted(self.examResult.scores, key=lambda x: x['score'], reverse=True)
        top_students = [s['student'] for s in sorted_students[:len(sorted_students) // 3]]
        bottom_students = [s['student'] for s in sorted_students[-len(sorted_students) // 3:]]
        return sorted_students, top_students, bottom_students

    def _analyze_single_question(self, question_id, question_data, top_students, bottom_students):
        """
        Analyzes a single question to compute difficulty and discrimination indices.
        """
        correct_answers, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students
        )
        difficulty_index = correct_answers / len(self.examResult.students)
        discrimination_index = self._compute_discrimination_index(
            question_id, top_students, bottom_students
        )
        difficulty_category = self._categorize_difficulty(difficulty_index)
        discrimination_category = self._categorize_discrimination(discrimination_index)

        return {
            'difficulty': difficulty_index,
            'difficulty_category': difficulty_category,
            'discrimination': discrimination_index,
            'discrimination_category': discrimination_category,
            'options': option_stats,
        }

    def _compute_option_stats(self, question_id, question_data, top_students, bottom_students):
        """
        Computes statistics for each option of a question.
        """
        correct_answers = 0
        total_student = len(self.examResult.students)
        option_stats = None

        for student in self.examResult.students:
            exam = next((ex for ex in self.examResult.exams if ex.code == student.exam_code), None)
            answer_order = exam.answer_order.get(question_id)
            # answer_order = exam.get_answer_order(question_id)
            # print("----------------", student.answers)
            if question_id in student.answers and answer_order is not None:
                correct_answer_index = exam.get_correct_answer(question_id)
                correct_answer = answer_order[correct_answer_index]
                student_answer = student.answers[question_id]['answer']
                # student_answer = student.answers[question_id]
                # selected_option = answer_order[student_answer]
                selected_option = correct_answer_index
                options = exam.question_bank.questions[question_id].get('options')
                current_option = options[selected_option]
                if selected_option == student_answer:
                    correct_answers = current_option.option_stats.get('correct_answers', 0)
                    # Increment the value
                    correct_answers += 1

                    # Update the dictionary with the new value
                    current_option.option_stats['correct_answers'] = correct_answers
                # option_stats[student_answer]['selected_by'] += 1
                # option_stats[student_answer]['ratio'] = option_stats[student_answer]['selected_by']/total_student
                current_option.option_stats['selected_by'] += 1
                current_option.option_stats['ratio'] = correct_answers/total_student
                if student in top_students:
                    current_option.option_stats['top_selected'] += 1
                if student in bottom_students:
                    current_option.option_stats['bottom_selected'] += 1
                option_stats = current_option.option_stats
        return correct_answers, option_stats

    def _compute_discrimination_index(self, question_id, top_students, bottom_students):
        """
        Calculates the discrimination index for a question.
        """
        if len(top_students) == 0 or len(bottom_students) == 0:
            return None

        top_correct = sum(
            1 for student in top_students
            if self.examResult.is_correct_answer(student, question_id)
        )
        bottom_correct = sum(
            1 for student in bottom_students
            if self.examResult.is_correct_answer(student, question_id)
        )
        return (top_correct / len(top_students)) - (bottom_correct / len(bottom_students))

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

