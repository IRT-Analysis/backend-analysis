class Exam:
    def __init__(self, code, question_bank, question_order=None, answer_order=None):
        """
        code: mã đề thi
        question_bank: đối tượng QuestionBank
        question_order: thứ tự các câu hỏi trong mã đề (tùy chỉnh)
        answer_order: thứ tự đáp án cho từng câu hỏi trong mã đề (tùy chỉnh)
        """
        self.code = code
        self.question_bank = question_bank
        self.question_order = question_order or list(
            question_bank.get_all_questions().keys()
        )  # Thứ tự câu hỏi trong mã đề
        self.answer_order = (
            answer_order or {}
        )  # Thứ tự đáp án cho từng câu hỏi trong mã đề (được khởi tạo)

        # Ánh xạ câu hỏi trong mã đề đến câu hỏi chuẩn
        # self.question_mapping = {f'Q{i+1}': self.question_order[i] for i in range(len(self.question_order))}

    def to_dict(self):
        return {
            "code": self.code,
            "question_order": self.question_order,
            "answer_order": {
                q_id: [option.to_dict() for option in options]
                for q_id, options in self.answer_order.items()
            },
        }

    def get_correct_answer(self, question_id):
        """Trả về chỉ số đáp án đúng trong câu hỏi chuẩn"""
        return self.question_bank.get_question(question_id)["correct_answer_index"]

    def get_question_content(self, question_id):
        """Trả về nội dung câu hỏi trong mã đề (theo thứ tự câu hỏi)"""
        question_mapping = self.question_mapping.get(question_id)
        if question_mapping:
            return self.question_bank.get_question(question_mapping)["content"]
        return None

    def get_question_options(self, question_id):
        """Trả về các lựa chọn trong câu hỏi của mã đề"""
        question_mapping = self.question_mapping.get(question_id)
        if question_mapping:
            return self.question_bank.get_question(question_mapping)["options"]
        return None

    def get_answer_order(self, question_id):
        """Trả về thứ tự đáp án cho câu hỏi trong mã đề"""
        return self.answer_order.get(question_id)
