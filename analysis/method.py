import numpy as np
import collections


class Method:
    def get_score_list(self, scores, max_score=60):
        score_list = [s["score"] for s in scores]
        score_counts = collections.Counter(score_list)

        array_of_score = [{key: score_counts[key]} for key in range(0, max_score + 1)]
        array_of_score = sorted(array_of_score, key=lambda x: list(x.keys())[0])

        return array_of_score

    def get_result_list(self, name, dict):
        print(name)
        list = []
        for key, value in dict.items():
            index = value[name] if value[name] is not None else 0
            list.append(index)
            print(key, index)
        step = 0.050
        max_value = max(list)

        ranges = []
        ranges.append({0.05: sum(1 for x in list if x < 0.050)})

        current_range = 0.100
        while current_range <= max_value + step:
            count = sum(
                1
                for x in list
                if round(current_range - step, 3) <= x < round(current_range, 3)
            )
            ranges.append({round(current_range, 3): count})
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

    def get_average_value(self, name, list):
        temp = [question[name] for question in list]
        if None in temp:
            return 0
        average = np.mean(temp)
        return round(average, 3)

    def get_student_detail(self):
        student_detail = []
        for student in self.examResult.scores:
            student_detail.append(
                {
                    "id": student["student"].id,
                    "firstName": student["student"].firstName,
                    "lastName": student["student"].lastName,
                    "exam_code": student["student"].exam_code,
                    "answers": student["student"].answers,
                    "score": student["score"],
                }
            )
        return student_detail

    def split_students(self):
        """
        Splits students into top and bottom groups based on scores.
        """
        sorted_students = sorted(
            self.examResult.scores, key=lambda x: x["score"], reverse=True
        )

        top_students = [
            s["student"] for s in sorted_students[: len(sorted_students) // 3]
        ]
        bottom_students = [
            s["student"] for s in sorted_students[-len(sorted_students) // 3 :]
        ]
        return sorted_students, top_students, bottom_students

    def _compute_option_stats(
        self, question_id, question_data, top_students, bottom_students, sorted_students
    ):
        """
        Computes statistics for each option of a question.
        """
        chosen_by = 0
        total_student = len(self.examResult.students)
        option_stats = {}
        top_students_len = len(top_students)
        bottom_students_len = len(bottom_students)

        # Precompute dictionaries for quick lookup
        exam_dict = {exam.code: exam for exam in self.examResult.exams}
        top_students_set = set(top_students)
        bottom_students_set = set(bottom_students)

        for student in self.examResult.students:
            exam = exam_dict.get(student.exam_code)
            if not exam:
                continue

            answer_order = exam.answer_order.get(question_id)
            if question_id not in student.answers or not answer_order:
                continue

            # correct_answer_index = exam.get_correct_answer(question_id)
            student_answer = student.answers[question_id]["answer"]

            for index, option in enumerate(answer_order):
                if student_answer != index:
                    option_stats[index] = option.option_stats
                    continue

                option.option_stats["selected_by"] += 1
                option.selected_students.append(student)
                option.option_stats["ratio"] = round(
                    option.option_stats["selected_by"] / total_student, 3
                )

                if student in top_students_set:
                    option.option_stats["top_selected"] += 1
                if student in bottom_students_set:
                    option.option_stats["bottom_selected"] += 1

                option.option_stats["discrimination"] = round(
                    (
                        option.option_stats["top_selected"] / top_students_len
                        - option.option_stats["bottom_selected"] / bottom_students_len
                    ),
                    3,
                )

                option.option_stats["r_pbis"] = self._calculate_option_rpbis(
                    sorted_students, option.selected_students
                )

                option_stats[index] = option.option_stats

        # Determine chosen_by
        chosen_by = max(option_stats, key=lambda x: option_stats[x]["selected_by"])
        return chosen_by, option_stats

    def _calculate_option_rpbis(self, all_students, selected_list):
        if len(all_students) == 0:
            return None

        all_scores = [
            self.examResult.scores[i] for i, student in enumerate(all_students)
        ]
        all_scores = [score["score"] for score in all_scores]

        selected_students = [
            student for student in all_students if student["student"] in selected_list
        ]

        not_selected_students = [
            student
            for student in all_students
            if student["student"] not in selected_list
        ]

        if len(selected_students) == 0 or len(not_selected_students) == 0:
            return 0

        selected_scores = [student["score"] for student in selected_students]
        not_selected_scores = [student["score"] for student in not_selected_students]
        selected_mean = np.mean(selected_scores)
        not_selected_mean = np.mean(not_selected_scores)

        total_std = np.std(all_scores)
        selected_proportion = len(selected_students) / len(all_students)
        not_selected_proportion = 1 - selected_proportion

        rpbis = (
            (selected_mean - not_selected_mean)
            / total_std
            * np.sqrt(selected_proportion * not_selected_proportion)
        )
        if rpbis is None:
            return 0
        return round(rpbis, 3)
