class Student:
    def __init__(self, id, firstName, lastName, exam_code, answers):
        """
        id: mssv
        name: tên thí sinh
        exam_code: mã đề thi của thí sinh
        answers: câu trả lời của thí sinh, dạng dict: {'Q1': 'answers',...) -> answers: {'answer': [-1,0,1,2,3,...], 'correct': True/False/None}
        """
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.exam_code = exam_code
        # -1: Not answer - 0, 1, 2, 3,...: A, B, C, D,..
        self.answers = answers

