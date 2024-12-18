import numpy as np

def get_average_score(student_list):
    """
        Args: List[Dict] [{"student": student_id, "score": score}]
    """
    scores = [student["score"] for student in student_list]
    return round(scores.mean(),3)

def get_average_rpbis():
    return 0

def get_average_discimination():
    return 0

def get_average_difficulty():
    return 0