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
        
    def two_pl_analysis(self):
        """
        Perform 2PL analysis on the exam.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        total_students = len(self.examResult.students)
        self.general_detail.update({
            "total_students": total_students,
            "total_questions": len(all_questions)
        })

        sorted_students, top_students, bottom_students = self.split_students()

        question_stats_list = [
            self._analyze_single_question_2pl(
                question_id,
                question_data,
                sorted_students,
                top_students,
                bottom_students
            ) for question_id, question_data in all_questions.items()
        ]

        self.question_stats.update({
            question_id: stat for question_id, stat in zip(all_questions.keys(), question_stats_list)
        })
        
        self.average_indexes.update({
            "average_score": self.get_average_value("score", self.examResult.scores),
            "average_discrimination": self.get_average_value("discrimination", question_stats_list),
            "average_difficulty": self.get_average_value("difficulty", question_stats_list),
        })

        return self.question_stats
    
    def _analyze_single_question_2pl(self, question_id, question_data, sorted_students, top_students, bottom_students):
        """
        Analyze a single question using 2PL model.
        """
        chosen_by, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students, sorted_students
        )

        response_data = self._get_response_data(question_id, sorted_students)
        response_data_top = self._get_response_data(question_id, top_students)
        response_data_bottom = self._get_response_data(question_id, bottom_students)

        # Fit the 2PL model
        model = Irt2PL()
        model.fit(response_data)

        # Calculate the difficulty and discrimination for the question
        difficulty, discrimination = model.get_params()

        # Calculate the separation and reliability
        separation, reliability = model.get_separation_reliability(response_data_top, response_data_bottom)

        question_bank = self.examResult.exams[0].question_bank
        content = question_bank.get_content(question_id)
        
        return {
            "content": content,
            "difficulty": difficulty,
            "discrimination": discrimination,
            "separation": separation,
            "reliability": reliability,
            "options": option_stats
        }
        
    def three_pl_analysis(self):
        """
        Perform 3PL analysis on the exam.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        total_students = len(self.examResult.students)
        self.general_detail.update({
            "total_students": total_students,
            "total_questions": len(all_questions)
        })

        sorted_students, top_students, bottom_students = self.split_students()

        question_stats_list = [
            self._analyze_single_question_3pl(
                question_id,
                question_data,
                sorted_students,
                top_students,
                bottom_students
            ) for question_id, question_data in all_questions.items()
        ]

        self.question_stats.update({
            question_id: stat for question_id, stat in zip(all_questions.keys(), question_stats_list)
        })
        
        self.average_indexes.update({
            "average_score": self.get_average_value("score", self.examResult.scores),
            "average_discrimination": self.get_average_value("discrimination", question_stats_list),
            "average_difficulty": self.get_average_value("difficulty", question_stats_list),
            "average_guessing": self.get_average_value("guessing", question_stats_list),
        })

        return self.question_stats
    
    def _analyze_single_question_3pl(self, question_id, question_data, sorted_students, top_students, bottom_students):
        """
        Analyze a single question using 3PL model.
        """
        chosen_by, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students, sorted_students
        )

        response_data = self._get_response_data(question_id, sorted_students)
        response_data_top = self._get_response_data(question_id, top_students)
        response_data_bottom = self._get_response_data(question_id, bottom_students)

        # Fit the 3PL model
        model = Irt3PL()
        model.fit(response_data)

        # Calculate the difficulty, discrimination and guessing for the question
        difficulty, discrimination, guessing = model.get_params()

        # Calculate the separation and reliability
        separation, reliability = model.get_separation_reliability(response_data_top, response_data_bottom)

        question_bank = self.examResult.exams[0].question_bank
        content = question_bank.get_content(question_id)
        
        return {
            "content": content,
            "difficulty": difficulty,
            "discrimination": discrimination,
            "guessing": guessing,
            "separation": separation,
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
    
class Irt2PL:
    def __init__(self):
        self.difficulty = 0.5
        self.discrimination = 1.0

    def fit(self, response_data, abilities=0.5, initial_difficulty=0.5, initial_discrimination=1.0):
        """
        Fit the 2PL model to the response data.
        """
        def likelihood(params, *args):
            difficulty, discrimination = params
            response_data = np.array(args[0], dtype=np.float64)
            prob = 1 / (1 + np.exp(-discrimination * (abilities - difficulty)))
            epsilon = 1e-10
            likelihood = np.sum(response_data * np.log(prob + epsilon) + (1 - response_data) * np.log(1 - prob + epsilon))
            return -likelihood
        initial_params = [initial_difficulty, initial_discrimination]
        result = minimize(likelihood, initial_params, args=(response_data), method='L-BFGS-B')
        self.difficulty, self.discrimination = result.x

    def get_params(self):
        """
        Get the estimated parameters of the 2PL model.
        """
        return self.difficulty, self.discrimination

    def get_probability(self, ability):
        """
        Calculate the probability of a correct response given the ability level.
        """
        prob = 1 / (1 + np.exp(self.discrimination * (self.difficulty - ability)))
        return prob

    def get_separation_reliability(self, response_data_top, response_data_bottom):
        """
        Calculate separation and reliability of the 2PL model.
        """
        mean_top = np.mean(response_data_top)
        mean_bottom = np.mean(response_data_bottom)
        separation = mean_top - mean_bottom
        reliability = separation / (1 + separation)
        return separation, reliability
    
class Irt3PL:
    def __init__(self):
        self.difficulty = None
        self.discrimination = None
        self.guessing = None
        
    def fit(self, response_data, abilitites=0.5, initial_difficulty=0.5, initial_discrimination=1.0, initial_guessing=0.25):
        """
        Fit the 3PL model to the response data.
        """
        def likelihood(params, *args):
            difficulty, discrimination, guessing = params
            response_data = np.array(args[0], dtype=np.float64)
            prob = guessing + (1 - guessing) / (1 + np.exp(discrimination * (difficulty - abilitites)))
            epsilon = 1e-10
            likelihood = np.sum(response_data * np.log(prob + epsilon) + (1 - response_data) * np.log(1 - prob + epsilon))
            return -likelihood
        initial_params = [initial_difficulty, initial_discrimination, initial_guessing]
        result = minimize(likelihood, initial_params, args=(response_data,), method='BFGS')
        self.difficulty, self.discrimination, self.guessing = result.x
        
    def get_params(self):
        """
        Get the estimated parameters of the 3PL model.
        """
        return self.difficulty, self.discrimination, self.guessing
    
    def get_probability(self, ability):
        """
        Calculate the probability of a correct response given the ability level.
        """
        prob = self.guessing + (1 - self.guessing) / (1 + np.exp(self.discrimination * (self.difficulty - ability)))
        return prob
    
    def get_separation_reliability(self, response_data_top, response_data_bottom):
        """
        Calculate separation and reliability of the 3PL model.
        """
        mean_top = np.mean(response_data_top)
        mean_bottom = np.mean(response_data_bottom)
        separation = mean_top - mean_bottom
        reliability = separation / (1 + separation)
        return separation, reliability
        
            
    