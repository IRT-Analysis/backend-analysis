from data_structure.question import QuestionBank 
from data_structure.exam import Exam
from data_structure.student import Student
from data_structure.examResult import ExamResult
from file_handling import result_file_process
from method.ctt_analysis import CttAnalysis

# Tạo bộ câu hỏi chuẩn
question_bank = QuestionBank()

# Thêm các câu hỏi vào bộ câu hỏi chuẩn
question_bank.add_question(
    'Q1', 
    'What is 2+2?', 
    ['A. 2', 'B. 4', 'C. 3', 'D. 5'], 
    1  # Đáp án đúng là 'B' với chỉ số 1
)

question_bank.add_question(
    'Q2', 
    'What is the capital of France?', 
    ['A. London', 'B. Paris', 'C. Rome', 'D. Berlin'], 
    1  # Đáp án đúng là 'B' với chỉ số 1
)

question_bank.add_question(
    'Q3', 
    'What is the color of the sky?', 
    ['A. Blue', 'B. Red', 'C. Green', 'D. Yellow'], 
    0  # Đáp án đúng là 'A' với chỉ số 0
)

# Tạo mã đề thi với câu hỏi và đáp án theo thứ tự yêu cầu
exam1 = Exam(
    code="Mã đề 1", 
    question_bank=question_bank, 
    question_order=['Q1', 'Q2', 'Q3'],
    answer_order={'Q1': [1, 2, 0, 3], 'Q2': [0, 1, 2, 3], 'Q3': [0, 1, 2, 3]}  # Thứ tự đáp án
)

exam2 = Exam(
    code="Mã đề 2", 
    question_bank=question_bank, 
    question_order=['Q3', 'Q1', 'Q2'],
    answer_order={'Q3': [3, 1, 0, 2], 'Q1': [3, 2, 0, 1], 'Q2': [0, 2, 1, 3]}  # Thứ tự đáp án cho mã đề 2
)

# Tạo danh sách thí sinh và câu trả lời của họ
students = [
    Student(id = 1, firstName="Thí sinh 1", lastName="..", exam_code="Mã đề 1", answers={'Q1': {'answer':0, 'correct': True}, 'Q2': {'answer':0, 'correct': True}, 'Q3': {'answer':0, 'correct': True}}),
    Student(id = 2, firstName="Thí sinh 2", lastName="..", exam_code="Mã đề 2", answers={'Q3': {'answer':0, 'correct': True}, 'Q1': {'answer':0, 'correct': True}, 'Q2': {'answer':0, 'correct': True} }),
    Student(id = 3, firstName="Thí sinh 3", lastName="..", exam_code="Mã đề 2", answers={'Q3': {'answer':0, 'correct': True}, 'Q1': {'answer':0, 'correct': True}, 'Q2': {'answer':0, 'correct': True} })
]

# Tạo kết quả thi và tính điểm
exam_result = ExamResult(exams=[exam1, exam2], students=students)
# scores = exam_result.calculate_scores()

# In kết quả
# Phân tích độ khó và độ phân biệt
ctt_analysis = CttAnalysis(exam_result)
ctt_analysis_result = ctt_analysis.analyze_questions_ctt()

# In kết quả
# print("Scores:", scores)
print("CTT Analysis:", ctt_analysis_result)

