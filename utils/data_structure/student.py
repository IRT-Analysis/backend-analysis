class Student:
    def __init__(self, id, firstName, lastName, exam_code, answers):
        """
        id: mssv
        name: tên thí sinh
        exam_code: mã đề thi của thí sinh
        answers: câu trả lời của thí sinh, dạng dict: {'Q1': index_answer, 'Q2': index_answer, ...}
        """
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.exam_code = exam_code
        self.answers = answers  # Lưu trữ câu trả lời của thí sinh dưới dạng chỉ số đáp án
