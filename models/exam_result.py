class ExamResult:
    def __init__(self, exams, students):
        """
        exams: danh sách các đối tượng Exam (nhiều mã đề)
        students: danh sách các đối tượng Student
        """
        self.exams = exams
        self.students = students
        self.scores = self.calculate_scores()  # Tính điểm cho từng thí sinh

    def calculate_scores(self):
        scores = []
        for student in self.students:
            exam = next(ex for ex in self.exams if ex.code == student.exam_code)
            score = 0
            
            # Duyệt qua tất cả câu hỏi trong mã đề và so sánh câu trả lời
            for question_id, answer_index in student.answers.items():
                answer_order = exam.get_answer_order(question_id)
                if answer_order is not None:
                    # Provide answer in the question bank
                    correct_answer_index = exam.get_correct_answer(question_id)
                    if correct_answer_index is not None:
                        correct_answer = answer_order[correct_answer_index]
                        student_answer = answer_order[answer_index['answer']]
                        if student_answer == correct_answer:
                            score += 1
                            student.answers[question_id]["correct"] = True
                        else:
                            student.answers[question_id]["correct"] = False
                    # Not prvode answer in the question bank
                    else:
                        student_answer = student.answers[question_id]["correct"]
                        exam.questions[question_id].correct_answer = student_answer
                        if student_answer is True:
                            score += 1
                        
            # Answer in the result file
            scores.append({'student': student, 'score': score})  # Lưu đối tượng student trực tiếp
        return scores

    def is_correct_answer(self, student, question_id):
        """
        Kiểm tra xem câu trả lời của sinh viên cho một câu hỏi có đúng không.
        """
        exam = next(ex for ex in self.exams if ex.code == student.exam_code)
        answer_order = exam.get_answer_order(question_id)
        
        if question_id in student.answers and answer_order is not None:
            correct_answer_index = exam.get_correct_answer(question_id)
            correct_answer = answer_order[correct_answer_index]
            student_answer = answer_order[student.answers[question_id]['answer']]
            return student_answer.content == correct_answer.content
        return False
    
    def get_student_response(self, student, question_id):
        """
        Lấy câu trả lời của sinh viên cho một câu hỏi.
        """
        exam = next(ex for ex in self.exams if ex.code == student.exam_code)
        answer_order = exam.get_answer_order(question_id)
        if question_id in student.answers and answer_order is not None:
            return student.answers[question_id]['answer']
        return None
    
    
    
