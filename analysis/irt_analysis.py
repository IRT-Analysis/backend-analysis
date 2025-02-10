import numpy as np
import pandas as pd
from scipy.optimize import minimize
from method import Model
class IRTModel:    
    def logistic(self, x):
        return 1 / (1 + np.exp(-x))

    def irt_log_likelihood(self, params):
        theta = params[:self.num_persons * self.num_factors].reshape(self.num_persons, self.num_factors)
        a = params[self.num_persons * self.num_factors:self.num_persons * self.num_factors + self.num_items * self.num_factors].reshape(self.num_items, self.num_factors)
        b = params[self.num_persons * self.num_factors + self.num_items * self.num_factors:]
        
        log_likelihood = 0
        for i in range(self.num_persons):
            for j in range(self.num_items):
                p_ij = self.logistic(np.dot(a[j], theta[i]) - b[j])
                log_likelihood += self.data[i, j] * np.log(p_ij) + (1 - self.data[i, j]) * np.log(1 - p_ij)
        return -log_likelihood

    def fit(self):
        initial_params = np.concatenate([self.theta.flatten(), self.a.flatten(), self.b])
        result = minimize(self.irt_log_likelihood, initial_params, method='L-BFGS-B')
        self.theta = result.x[:self.num_persons * self.num_factors].reshape(self.num_persons, self.num_factors)
        self.a = result.x[self.num_persons * self.num_factors:self.num_persons * self.num_factors + self.num_items * self.num_factors].reshape(self.num_items, self.num_factors)
        self.b = result.x[self.num_persons * self.num_factors + self.num_items * self.num_factors:]

    def predict(self):
        probabilities = np.zeros((self.num_persons, self.num_items))
        for i in range(self.num_persons):
            for j in range(self.num_items):
                probabilities[i, j] = self.logistic(np.dot(self.a[j], self.theta[i]) - self.b[j])
        return probabilities

# Example usage
if __name__ == "__main__":
    # Example data: rows are persons, columns are items, values are 0 or 1
    data = np.array([
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 1, 1, 0],
        [0, 0, 0, 1]
    ])
    
    irt_model = IRTModel(data)
    irt_model.fit()
    probabilities = irt_model.predict()
    print(probabilities)