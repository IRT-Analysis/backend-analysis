from analysis.method import Model
# from irt import two_parameter_model
import numpy as np
from scipy.optimize import minimize
from models.student import Student
from math import sqrt

class IrtAnalysis(Model):
    response_list = []
    prob_list = []

    def __init__(self, examResult):
        self.examResult = examResult
        self.general_detail = {}
        self.average_indexes = {}
        self.question_stats = {}
        self.participant_abilities = {}

    def _get_response_data(self, question_id, sorted_students):
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

    def get_model(self, model):
        if model == "Rasch":
            return self.rasch_analysis()
        elif model == "2PL":
            return self.two_pl_analysis()
        elif model == "3PL":
            return self.three_pl_analysis()
        else:
            return None

    # def rasch_analysis(self):
    #     all_questions = self.examResult.exams[0].question_bank.get_all_questions()
    #     total_students = len(self.examResult.students)
    #     self.general_detail.update({
    #         "total_students": total_students,
    #         "total_questions": len(all_questions)
    #     })

    #     sorted_students, top_students, bottom_students = self.split_students()

    #     question_stats_list = [
    #         self._analysis_single_question_rasch(
    #             question_id,
    #             question_data,
    #             sorted_students,
    #             top_students,
    #             bottom_students,
    #             difficulty=0.5
    #         ) for question_id, question_data in all_questions.items()
    #     ]

    #     self.question_stats.update({
    #         question_id: stat for question_id, stat in zip(all_questions.keys(), question_stats_list)
    #     })

    #     self.average_indexes.update({
    #         "average_score": self.get_average_value("score", self.examResult.scores),
    #         "average_difficulty": self.get_average_value("difficulty", question_stats_list),
    #         "average_separation": self.get_average_value("separation", question_stats_list),
    #         "average_reliability": self.get_average_value("reliability", question_stats_list),
    #         "item_infit": self.get_average_value("infit", question_stats_list),
    #         "item_outfit": self.get_average_value("outfit", question_stats_list),
    #     })

    #     # Calculate ability for each participant
    #     for student in sorted_students:
    #         response_data = [1 if self.examResult.is_correct_answer(student['student'], question_id) else 0 for question_id in all_questions]
    #         ability_estimate = RaschModel([q["difficulty"] for q in self.question_stats.values()]).estimate_ability(response_data)
    #         self.participant_abilities[student['student']] = ability_estimate
    #         student['student'].ability = ability_estimate 

    #     return self.question_stats
    
    def rasch_analysis(self):
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        total_students = len(self.examResult.students)

        self.general_detail.update({
            "total_students": total_students,
            "total_questions": len(all_questions)
        })

        sorted_students, top_students, bottom_students = self.split_students()
        
        # Initialize difficulties
        question_difficulties = {q_id: 0.5 for q_id in all_questions.keys()}
        
        # Iterate to refine difficulties and abilities
        max_iterations = 20
        tol = 1e-4
        
        for _ in range(max_iterations):
            # Step 1: Estimate student abilities using current question difficulties
            student_abilities = {}
            for student in sorted_students:
                response_data = [1 if self.examResult.is_correct_answer(student['student'], q_id) else 0 for q_id in all_questions]
                ability_estimate = RaschModel().estimate_ability(response_data, np.array(list(question_difficulties.values())))
                student_abilities[student['student']] = ability_estimate
                student['student'].ability = ability_estimate

            # Step 2: Estimate question difficulties using current student abilities
            new_question_difficulties = {}
            for q_id in all_questions.keys():
                response_data = np.array([1 if self.examResult.is_correct_answer(student['student'], q_id) else 0 for student in sorted_students])
                ability_levels = np.array([student_abilities[student['student']] for student in sorted_students])
                new_question_difficulties[q_id] = RaschModel().estimate_difficulty(response_data, ability_levels)
            
            # Check for convergence
            if all(abs(new_question_difficulties[q] - question_difficulties[q]) < tol for q in all_questions.keys()):
                break
            question_difficulties = new_question_difficulties

        # Step 3: Store final question statistics
        question_stats_list = [
            self._analysis_single_question_rasch(
                q_id, all_questions[q_id], sorted_students, top_students, bottom_students, difficulty=question_difficulties[q_id]
            ) for q_id in all_questions.keys()
        ]

        self.question_stats.update({
            q_id: stat for q_id, stat in zip(all_questions.keys(), question_stats_list)
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

    # def _analysis_single_question_rasch(self, question_id, question_data, sorted_students, top_students, bottom_students, difficulty=0.5):
    #     chosen_by, option_stats = self._compute_option_stats(
    #         question_id, question_data, top_students, bottom_students, sorted_students
    #     )

    #     response_data = self._get_response_data(question_id, sorted_students)
    #     response_data_top = self._get_response_data(question_id, top_students)
    #     response_data_bottom = self._get_response_data(question_id, bottom_students)

    #     # Fit the Rasch model
    #     model = RaschModel(0.5, 0.5)
    #     model.fit(response_data)

    #     # Calculate the difficulty for the question
    #     item_difficulty, person_ability, infit, outfit = model.get_params()
    #     self.prob_list.append(1 / (1 + np.exp(item_difficulty - person_ability)))
    #     self.response_list.append(response_data)

    #     # Calculate the separation and reliability
    #     separation, reliability = model.calculate_separation_reliability(response_data_top, response_data_bottom)

    #     question_bank = self.examResult.exams[0].question_bank
    #     content = question_bank.get_content(question_id)

    #     return {
    #         "content": content,
    #         "difficulty": item_difficulty,
    #         "separation": separation,
    #         "personal_ability": person_ability,
    #         "logit": item_difficulty - person_ability,
    #         "infit": infit,
    #         "outfit": outfit,
    #         "reliability": reliability,
    #         "options": option_stats
    #     }
    
    def _analysis_single_question_rasch(self, question_id, question_data, sorted_students, top_students, bottom_students, difficulty):
        chosen_by, option_stats = self._compute_option_stats(
            question_id, question_data, top_students, bottom_students, sorted_students
        )

        response_data = self._get_response_data(question_id, sorted_students)
        response_data_top = self._get_response_data(question_id, top_students)
        response_data_bottom = self._get_response_data(question_id, bottom_students)

        # Use precomputed student abilities from rasch_analysis
        ability_levels = np.array([student['student'].ability for student in sorted_students])

        # Compute probability of correct response using the estimated difficulty
        # prob_correct = 1 / (1 + np.exp(difficulty - ability_levels.mean()))
        # self.prob_list.append(prob_correct)
        # self.response_list.append(response_data)

        # Compute separation and reliability
        separation, reliability = self.calculate_separation_reliability(response_data_top, response_data_bottom)

        # Get question content
        question_bank = self.examResult.exams[0].question_bank
        content = question_bank.get_content(question_id)
        
        # Calculate infot, outfit value
        infit, outfit = self._calculate_infit_outfit(response_data, difficulty, sorted_students)

        return {
            "content": content,
            "difficulty": difficulty,  # Directly use the precomputed difficulty
            "separation": separation,
            "personal_ability": ability_levels.mean(),
            "logit": difficulty - ability_levels.mean(),
            "infit": infit,  # Remove redundant infit/outfit computation
            "outfit": outfit,  # These should be computed once in rasch_analysis
            "reliability": reliability,
            "options": option_stats
        }

    def get_average_value(self, key, data):
        return np.mean([d[key] for d in data if key in d])
    
    def calculate_separation_reliability(self, response_data_top, response_data_bottom):
        separation = np.mean(response_data_top) - np.mean(response_data_bottom)
        reliability = 1 - (1 / (1 + separation ** 2))
        return separation, reliability
           
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

    def _calculate_infit_outfit(self, response_data, difficulty, sorted_students):
        """
        Calculate the infit and outfit statistics for a given question.
        """
        ability_levels = np.array([student['student'].ability for student in sorted_students])

        # Compute probabilities of correct responses (avoid extreme values)
        p_list = [1 / (1 + np.exp(difficulty - ability)) for ability in ability_levels]

        # Compute standardized residuals (z-scores)
        z_list = [(x - p) / np.sqrt(p * (1 - p)) for x, p in zip(response_data, p_list)]

        # Compute infit and outfit statistics
        infit = np.sum([(p * (1 - p) * (z ** 2)) for p, z in zip(p_list, z_list)]) / np.sum([p * (1 - p) for p in p_list])
        outfit = np.mean([z ** 2 for z in z_list])

        return infit, outfit

    
class RaschModel:
    # def __init__(self, item_difficulty=0.5, person_ability=0.5):
    #     self.item_difficulty = item_difficulty
    #     self.person_ability = person_ability

    # def calculate_prob(self, theta, beta):
    #     return 1 / (1 + np.exp(beta - theta))

    # def negative_log_likelihood(self, theta, response_data):
    #     likelihood = 0
    #     for response, beta in zip(response_data, self.item_difficulty):
    #         prob = self.calculate_prob(theta, beta)
    #         likelihood += response * np.log(prob + 1e-10) + (1 - response) * np.log(1 - prob + 1e-10)
    #     return -likelihood

    # def estimate_ability(self, response_data):
    #     initial_theta = 0
    #     result = minimize(self.negative_log_likelihood, initial_theta, args=(response_data,), method='BFGS')
    #     return result.x[0] if result.success else None

    # def fit(self, response_data):
    #     def likelihood(params, *args):
    #         item_difficulty, person_ability = params
    #         response_data = np.array(args[0], dtype=np.float64)
    #         prob = 1 / (1 + np.exp(item_difficulty - person_ability))
    #         self.infit = self.calculate_infit(prob, response_data)
    #         self.outfit = self.calculate_outfit(prob, response_data)
    #         epsilon = 1e-10
    #         likelihood = np.sum(response_data * np.log(prob + epsilon) + (1 - response_data) * np.log(1 - prob + epsilon))
    #         return -likelihood

    #     initial_params = [self.item_difficulty, self.person_ability]
    #     result = minimize(likelihood, initial_params, args=(response_data,), method='BFGS')

    #     # Check for successful convergence
    #     if result.success:
    #         self.item_difficulty, self.person_ability = result.x
    #     else:
    #         print("Optimization did not converge")

    # def get_params(self):
    #     return self.item_difficulty, self.person_ability, self.infit, self.outfit

    # def calculate_infit(self, prob, response_data):
    #     weighted_residuals = (response_data - prob) ** 2
    #     expected_variance = prob * (1 - prob)
    #     infit = np.sum(weighted_residuals) / np.sum(expected_variance)
    #     return infit

    # def calculate_outfit(self, prob, response_data):
    #     outfit = np.sum((response_data - prob) ** 2) / np.sum(prob * (1 - prob))
    #     return outfit

    # def calculate_separation_reliability(self, response_data_top, response_data_bottom):
    #     separation = np.mean(response_data_top) - np.mean(response_data_bottom)
    #     reliability = 1 - (1 / (1 + separation ** 2))
    #     return separation, reliability
    def __init__(self, difficulty_init=0.5):
        self.difficulty = difficulty_init

    def estimate_ability(self, response_data, difficulty_levels, max_iter=10, tol=1e-4):
        """Iteratively estimate ability given response data and question difficulties."""
        ability = 0.0  # Initial ability
        for _ in range(max_iter):
            logit_sum = sum(difficulty_levels)
            p_correct = 1 / (1 + np.exp(difficulty_levels - ability))
            ability_new = ability + np.sum(response_data - p_correct) / logit_sum
            
            if abs(ability_new - ability) < tol:
                break
            ability = ability_new
        return ability

    def estimate_difficulty(self, response_data, ability_levels, max_iter=10, tol=1e-4):
        """Iteratively estimate difficulty given response data and student abilities."""
        difficulty = self.difficulty  # Initial difficulty
        for _ in range(max_iter):
            p_correct = 1 / (1 + np.exp(difficulty - ability_levels))
            difficulty_new = difficulty + np.sum(p_correct - response_data) / len(response_data)

            if abs(difficulty_new - difficulty) < tol:
                break
            difficulty = difficulty_new
        return difficulty

    def get_params(self):
        return self.difficulty
    
    def calculate_prob(self, theta, beta):
        return 1 / (1 + np.exp(beta - theta))
       
class Irt2PL:
    def __init__(self):
        self.difficulty = 0.5
        self.discrimination = 1.0

    def fit(self, response_data, abilities=0.25, initial_difficulty=0.5, initial_discrimination=1.0):
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
        
            
    