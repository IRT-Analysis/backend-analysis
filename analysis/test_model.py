import numpy as np
from py_irt.models.one_param_logistic import OneParamLog
from py_irt.models.two_param_logistic import TwoParamLog
from analysis.method import Model
import torch

class TestModel(Model):
    
    def __init__(self, examResult, model_type='1PL'):
        super().__init__(examResult)
        self.general_detail = {}
        self.average_indexes = {}
        self.question_stats = {}
        self.model_type = model_type

    def analyze_questions_irt(self):
        """
        Main function to analyze questions using IRT.
        """
        all_questions = self.examResult.exams[0].question_bank.get_all_questions()
        total_students = len(self.examResult.students)
        self.general_detail.update({
            "total_students": total_students,
            "total_questions": len(all_questions)
        })

        # Prepare response data for IRT analysis
        responses, items, models = self._prepare_responses()

        # Initialize and fit the IRT model
        irt_model = self._fit_irt_model(models, items, responses)
        
        item_difficulties = irt_model.item_difficulties_
        abilities = irt_model.abilities_
        
        if self.model_type == '2PL':
            item_discriminations = irt_model.item_discriminations_

        # Analyze each question
        question_stats_list = [
            self._analyze_single_question(
                question_id, question_data, item_difficulties, abilities, item_discriminations if self.model_type == '2PL' else None
            ) for question_id, question_data in all_questions.items()
        ]

        self.average_indexes.update({
            "average_difficulty": np.mean(item_difficulties)
        })

        if self.model_type == '2PL':
            self.average_indexes.update({
                "average_discrimination": np.mean(item_discriminations)
            })

        self.question_stats.update({
            question_id: stat for question_id, stat in zip(all_questions.keys(), question_stats_list)
        })
        
        return self.question_stats

    def _prepare_responses(self):
        """
        Prepare the responses for IRT analysis.
        """
        responses = []
        for student in self.examResult.students:
            answers = [
                1 if self.examResult.is_correct_answer(student, question_id)
                else 0
                for question_id in self.examResult.exams[0].question_bank.get_all_questions().keys()
            ]
            responses.append(answers)
        
        # Create items and models arrays
        items = np.arange(len(responses[0]))
        models = torch.arange(1)  # Create a single model for simplicity
        return np.array(responses), items, models

    def _fit_irt_model(self, models, items, responses):
        """
        Fit the IRT model to the response data.
        """
        # Define priors
        num_items = responses.shape[1]
        priors = "vague"
        if self.model_type == '2PL':
            priors["discrimination"] = {
                "mean": np.ones(num_items),
                "std": np.ones(num_items),
                "type": "normal"
            }

        device = "cpu"  # or "cuda" if GPU is available

        # Initialize and fit the IRT model
        if self.model_type == '1PL':
            irt_model = OneParamLog(priors, device, num_items, len(models))
        elif self.model_type == '2PL':
            irt_model = TwoParamLog(priors, device, num_items, len(models))
        else:
            raise ValueError("Unsupported model type. Choose '1PL' or '2PL'.")

        num_epochs = 100
        responses = np.array(responses)  # Ensure NumPy array
        responses = torch.tensor(responses, dtype=torch.float32)  # Convert to PyTorch tensor
        models = torch.tensor(models, dtype=torch.int64)
        items = torch.tensor(items, dtype=torch.int64)

        irt_model.fit(models=irt_model, items=items, responses=responses, num_epochs=num_epochs)
        return irt_model

    def _analyze_single_question(self, question_id, question_data, item_difficulties, abilities, item_discriminations):
        """
        Analyze a single question using IRT.
        """
        question_stats = {
            "content": question_data["content"],
            "difficulty": item_difficulties[question_id],
            "discrimination": item_discriminations[question_id] if item_discriminations is not None else None,
            "correct_percentage": self._calculate_correct_percentage(question_id, abilities)
        }
        return question_stats
    
    def _compute_probability_of_correct_response(self, ability, difficulty, discrimination=None):
        """
        Computes the probability of a correct response for a given ability level.
        """
        if discrimination is None:
            return 1 / (1 + np.exp(-(ability - difficulty)))
        else:
            return 1 / (1 + np.exp(-discrimination * (ability - difficulty)))