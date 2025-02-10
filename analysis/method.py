import numpy as np
import collections
class Method:
    def get_score_list(self, scores, max_score = 60):
        score_list = [s["score"] for s in scores]
        score_counts = collections.Counter(score_list)
        
        array_of_score = [{key: score_counts[key]} for key in range(0, max_score + 1)]
        array_of_score = sorted(array_of_score, key=lambda x: list(x.keys())[0])
        
        return array_of_score


    def get_result_list(self, name, dict):
        list = []
        for key, value in dict.items():
            index = value[name] if value[name] is not None else 0
            list.append(index)
        step = 0.050
        max_value = max(list)
        
        ranges = []
        ranges.append({0.05: sum(1 for x in list if x < 0.050)})

        current_range = 0.100
        while current_range <= max_value + step:
            count = sum(1 for x in list if round(current_range - step,3) <= x < round(current_range,3))
            ranges.append({round(current_range,3): count})
            current_range += step
        return ranges
    
class Model:
    examResult = None
    question_stats = {}
    average_indexes = {}
    general_detail = {}
    
    def __init__(self, examResult):
        self.examResult = examResult
        self.general_detail = {
            "total_students": 0,
            "total_questions": 0,
            "total_option": 4,
        }
        
    def get_student_detail(self):
        student_detail = []
        for student in self.examResult.scores:
            student_detail.append({
                "id": student["student"].id,
                "firstName": student["student"].firstName,
                "lastName": student["student"].lastName,
                "exam_code": student["student"].exam_code,
                "answers": student["student"].answers,
                "score": student["score"], 
            })
        return student_detail