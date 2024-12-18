class Option:
    option_stats = {
        "correct_answer": 0,
        "selected_by": 0,
        "top_selected": 0,
        "bottom_selected": 0,
        "ratio": 0,
    }

    def __init__(self, content):
        self.content = content
        self.option_stats = {
            "correct_answer": 0,
            "selected_by": 0,
            "top_selected": 0,
            "bottom_selected": 0,
            "ratio": 0,
        }


class QuestionBank:
    def __init__(self):
        """Quản lý bộ câu hỏi chuẩn"""
        self.questions = {}

    def add_question(
        self, question_id, question_content, options, correct_answer_index=None
    ):
        """
        Thêm câu hỏi vào bộ câu hỏi chuẩn
        """
        self.questions[question_id] = {
            "content": question_content,
            "options": options,
            "correct_answer_index": correct_answer_index,
        }

    def get_question(self, question_id):
        """Trả về câu hỏi theo mã câu hỏi"""
        return self.questions.get(question_id)

    def get_all_questions(self):
        """Trả về toàn bộ bộ câu hỏi chuẩn"""
        return self.questions
