class CttAnalysis:
    examResult = None    
    def __init__(self, examResult):
        self.examResult = examResult
        
    def analyze_questions_ctt(self):
        """
        Phân tích độ khó và độ phân biệt cho từng câu hỏi trong QuestionBank,
        đồng thời tính các chỉ số này cho từng lựa chọn.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        
        # Chia sinh viên thành nhóm điểm cao và điểm thấp
        sorted_students = sorted(self.examResult.scores, key=lambda x: x['score'], reverse=True)
        top_students = [s['student'] for s in sorted_students[:len(sorted_students) // 3]]
        bottom_students = [s['student'] for s in sorted_students[-len(sorted_students) // 3:]]

        question_stats = {}

        for question_id, question_data in all_questions.items():
            correct_answers = 0
            option_stats = {}
            
            # Lấy danh sách lựa chọn của câu hỏi
            options = question_data['options']

            # Initialize counts for each option
            for option_index in range(len(options)):
                option_stats[option_index] = {
                    'selected_by': 0,
                    'top_selected': 0,
                    'bottom_selected': 0
                }

            for student in self.examResult.students:
                exam = next(ex for ex in self.examResult.exams if ex.code == student.exam_code)
                answer_order = exam.get_answer_order(question_id)
                
                if question_id in student.answers and answer_order is not None:
                    correct_answer_index = exam.get_correct_answer(question_id)
                    correct_answer = answer_order[correct_answer_index]
                    student_answer = student.answers[question_id]
                    selected_option = answer_order[student_answer]
                    
                    # Check if the answer is correct
                    if selected_option == correct_answer:
                        correct_answers += 1

                    # Update option stats
                    option_index = student_answer
                    option_stats[option_index]['selected_by'] += 1
                    if student in top_students:
                        option_stats[option_index]['top_selected'] += 1
                    if student in bottom_students:
                        option_stats[option_index]['bottom_selected'] += 1

            # Tính chỉ số độ khó (difficulty_index)
            difficulty_index = correct_answers / len(self.examResult.students)

            # Tính chỉ số độ phân biệt (discrimination_index)
            if len(top_students) > 0 and len(bottom_students) > 0:
                top_correct = sum(
                    1 for student in top_students
                    if self.examResult.is_correct_answer(student, question_id)
                )
                bottom_correct = sum(
                    1 for student in bottom_students
                    if self.examResult.is_correct_answer(student, question_id)
                )

                discrimination_index = (top_correct / len(top_students)) - (bottom_correct / len(bottom_students))
            else:
                # Đặt giá trị mặc định nếu không đủ sinh viên
                discrimination_index = None

            # Compute difficulty and discrimination for each option
            for option, stats in option_stats.items():
                stats['difficulty'] = stats['selected_by'] / len(self.examResult.students)
                if len(top_students) > 0 and len(bottom_students) > 0:
                    stats['discrimination'] = (
                        stats['top_selected'] / len(top_students)
                        - stats['bottom_selected'] / len(bottom_students)
                    )
                else:
                    stats['discrimination'] = None

            question_stats[question_id] = {
                'difficulty': difficulty_index,
                'discrimination': discrimination_index,
                'options': option_stats
            }

        return question_stats