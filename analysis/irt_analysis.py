from analysis.method import Model
# from irt import two_parameter_model
import numpy as np
from scipy.optimize import minimize
from models.student import Student


class IrtAnalysis(Model):
    response_list = []
    prob_list = []
    
    def __init__(self, examResult):
        self.examResult = examResult
        self.general_detail = {}
        self.average_indexes = {}
        self.question_stats = {}
        
    # def analyze_questions_irt(self):
    #     """
    #     Main function to analyze questions using IRT model.
    #     """
    #     all_questions = self.examResult.exams[0].question_bank.get_all_questions()
    #     total_students = len(self.examResult.students)
    #     self.general_detail.update({
    #         "total_students": total_students,
    #         "total_questions": len(all_questions)
    #     })

    #     sorted_students, top_students, bottom_students = self.split_students()

    #     question_stats_list = [
    #         self._analyze_single_question_irt(
    #             question_id,
    #             question_data,
    #             sorted_students,
    #             top_students,
    #             bottom_students,
    #             difficulty=0.5,  # Example value
    #             discrimination=1.0  # Example value
    #         ) for question_id, question_data in all_questions.items()
    #     ]

    #     self.average_indexes.update({
    #         "average_score": self.get_average_value("score", self.examResult.scores),
    #         "average_discrimination": self.get_average_value("discrimination", question_stats_list),
    #         "average_difficulty": self.get_average_value("difficulty", question_stats_list),
    #         # "average_rpbis": self.get_average_value("rpbis", question_stats_list)
    #     })

    #     self.question_stats.update({
    #         question_id: stat for question_id, stat in zip(all_questions.keys(), question_stats_list)
    #     })

    #     return self.question_stats

    # def _analyze_single_question_irt(self, question_id, question_data, sorted_students, top_students, bottom_students, difficulty=0.5, discrimination=1.0):
    #     """
    #     Analyze a single question using IRT model.
    #     """
    #     response_data = self._get_response_data(question_id, sorted_students)
    #     # response_data_top = self._get_response_data(question_id, top_students)
    #     # response_data_bottom = self._get_response_data(question_id, bottom_students)

    #     # Fit the IRT model
    #     model = two_parameter_model(0.5, 0.5, 0.5)
    #     model.fit(response_data, difficulty, discrimination)

    #     # Calculate the discrimination and difficulty for the question
    #     discrimination, difficulty = model.get_params()

    #     # Calculate the RPBIS
    #     # r_pbis = model.get_rpbis(response_data_top, response_data_bottom)

    #     return {
    #         "model": model,
    #         "discrimination": discrimination,
    #         "difficulty": difficulty,
    #         # "r_pbis": r_pbis
    #     }

    def _get_response_data(self, question_id, sorted_students):
        """
        Get response data for IRT model fitting.
        """
        response_data = []
        for student in sorted_students:
            if type(student) is Student:
                if self.examResult.is_correct_answer(student, question_id):
                    response_data.append(1)
                else:
                    response_data.append(0)
            else:
                if self.examResult.is_correct_answer(student['student'], question_id):
                    response_data.append(1)
                else:
                    response_data.append(0)
        return response_data
    
    def rasch_analysis(self):
        """
        Perform Rasch analysis on the exam.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        total_students = len(self.examResult.students)
        self.general_detail.update({
            "total_students": total_students,
            "total_questions": len(all_questions)
        })

        sorted_students, top_students, bottom_students = self.split_students()

        question_stats_list = [
            self._analysis_single_question_rasch(
                question_id,
                question_data,
                sorted_students,
                top_students,
                bottom_students,
                difficulty=0.5 
            ) for question_id, question_data in all_questions.items()
        ]

        self.question_stats.update({
            question_id: stat for question_id, stat in zip(all_questions.keys(), question_stats_list)
        })
                
        self.average_indexes.update({
            "average_score": self.get_average_value("score", self.examResult.scores),
            "average_difficulty": self.get_average_value("difficulty", question_stats_list),
            "average_separation": self.get_average_value("separation", question_stats_list),
            "average_reliability": self.get_average_value("reliability", question_stats_list),
            "item_infit": self.get_average_value("infit", question_stats_list),
            "item_outfit": self.get_average_value("outfit", question_stats_list),
        })
        return self.question_stats
    
    def _analysis_single_question_rasch(self, question_id, question_data, sorted_students, top_students, bottom_students, difficulty=0.5):
        """
        Analyze a single question using Rasch model.
        """
        chosen_by, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students, sorted_students
        )
        
        response_data = self._get_response_data(question_id, sorted_students)
        response_data_top = self._get_response_data(question_id, top_students)
        response_data_bottom = self._get_response_data(question_id, bottom_students)

        # Fit the Rasch model
        model = RaschModel(0.5, 0.5)
        model.fit(response_data, difficulty)

        # Calculate the difficulty for the question
        item_difficulty, person_ability, infit, outfit, prob = model.get_params()
        self.prob_list.append(prob)
        self.response_list.append(response_data)

        # Calculate the separation and reliability
        separation, reliability = model.get_separation_reliability(response_data_top, response_data_bottom)

        question_bank = self.examResult.exams[0].question_bank
        content = question_bank.get_content(question_id)
        
        return {
            "content": content,
            "difficulty": item_difficulty,
            "separation": separation,
            "personal_ability": person_ability,
            "logit": item_difficulty-person_ability,
            "infit": infit,
            "outfit": outfit,
            "reliability": reliability,
            "options": option_stats
        }
        
class RaschModel:
    def __init__(self, item_difficulty=0.5, person_ability=0.5, infit=1, outfit=1, prob = 0):
        self.item_difficulty = item_difficulty
        self.person_ability = person_ability
        self.infit = infit
        self.outfit = outfit
        self.prob = prob

    def fit(self, response_data, difficulty=0.5):
        def likelihood(params, *args):
            item_difficulty, person_ability = params
            response_data = np.array(args[0], dtype=np.float64)
            prob = 1 / (1 + np.exp(item_difficulty - person_ability))
            self.infit = self.calculate_infit(prob, response_data)
            self.outfit = self.calculate_outfit(prob, response_data)
            self.prob = prob
            epsilon = 1e-10
            likelihood = np.sum(response_data * np.log(prob + epsilon) + (1 - response_data) * np.log(1 - prob + epsilon))
            return -likelihood
        initial_params = [self.item_difficulty, self.person_ability]
        result = minimize(likelihood, initial_params, args=(response_data,), method='BFGS')

        # Check for successful convergence
        if result.success:
            self.item_difficulty, self.person_ability = result.x
        else:
            print("Optimization did not converge")

    def get_params(self):
        return self.item_difficulty, self.person_ability, self.infit, self.outfit, self.prob

    def get_separation_reliability(self, response_data_top, response_data_bottom):
        separation = np.mean(response_data_top) - np.mean(response_data_bottom)
        reliability = 1 - (1 / (1 + separation**2))
        return separation, reliability
    
    def calculate_infit(self, prob, response_data):
        x = 0
        y = 0
        for i in range(len(response_data)):
            x += (response_data[i] - prob)**2
            y += prob * (1 - prob)
        return x/y
    
    def calculate_outfit(self, prob, response_data):
        return np.sum((response_data - prob)**2) / (prob * (1 - prob)*len(response_data))

    def calculate_person_outfit(self, prob, response_data):
        return 0
        
    
    