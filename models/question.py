class Option:
    option_stats = {
        "selected_by": 0,
        "top_selected": 0,
        "bottom_selected": 0,
        "ratio": 0,
    }

    def __init__(self, content):
        self.content = content
        self.option_stats = {
            "selected_by": 0,
            "top_selected": 0,
            "bottom_selected": 0,
            "ratio": 0,
            "discrimination": 0,
            "r_pbis": 0,
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

    def get_content(self, question_id):
        options = [option.content for option in self.questions[question_id]["options"]]
        content = {
            "question": self.questions[question_id]["content"],
            "option": options,
        }
        return content

    def get_correct_answer_index(self, question_id):
        return self.questions[question_id]["correct_answer_index"]
