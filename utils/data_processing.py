import pandas as pd
import numpy as np
from typing import Dict, Any, List


def calculate_rpbis_for_key(
    question_data: pd.Series, key: Any, total_scores: pd.Series
) -> float:
    key_responses = (question_data == key).astype(int)
    X_p = total_scores[key_responses == 1].mean()
    X_q = total_scores[key_responses == 0].mean()
    S_t = total_scores.std()
    p = key_responses.mean()
    q = 1 - p
    if S_t == 0:
        return 0
    return (X_p - X_q) / S_t * np.sqrt(p * q)


def analyze_item(
    question_data: pd.Series,
    correct_answer: Any,
    total_scores: pd.Series,
    high_group: pd.DataFrame,
    low_group: pd.DataFrame,
) -> Dict[str, Any]:
    results = {}
    answer_distribution = question_data.value_counts(normalize=True) * 100
    high_group_count = question_data.loc[high_group.index].value_counts()
    low_group_count = question_data.loc[low_group.index].value_counts()
    mean_scores = {}
    discrimination = {}
    rpbis_results = {}

    for answer in question_data.unique():
        mean_scores[answer] = total_scores[question_data == answer].mean()
        P_high = (
            high_group_count.get(answer, 0) / len(high_group)
            if len(high_group) > 0
            else 0
        )
        P_low = (
            low_group_count.get(answer, 0) / len(low_group) if len(low_group) > 0 else 0
        )
        discrimination[answer] = P_high - P_low
        rpbis_results[answer] = calculate_rpbis_for_key(
            question_data, answer, total_scores
        )

    correct_responses = (question_data == correct_answer).astype(int)
    difficulty = correct_responses.mean() * 100

    results["distribution"] = answer_distribution.to_dict()
    results["mean_scores"] = mean_scores
    results["high_group"] = high_group_count.to_dict()
    results["discrimination"] = discrimination
    results["low_group"] = low_group_count.to_dict()
    results["difficulty"] = difficulty
    results["rpbis"] = rpbis_results

    return results


def process_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Processes the dataframe and returns the analysis results as an array."""
    correct_answers = df.iloc[0, 4:]
    student_answers = df.iloc[1:, 4:]
    total_scores = student_answers.eq(correct_answers).sum(axis=1)
    student_answers["Total Score"] = total_scores

    # Sort students by their total score
    df_sorted = student_answers.sort_values(by="Total Score", ascending=True)
    low_group = df_sorted.head(int(0.27 * len(student_answers)))
    high_group = df_sorted.tail(int(0.27 * len(student_answers)))

    # Analyze each question
    analysis_results = []  # Use a list instead of a dictionary
    columns_to_analyze = student_answers.columns[:-1]  # Exclude 'Total Score'

    for col in columns_to_analyze:
        question_data = student_answers[col]
        correct_answer = correct_answers[col]
        results = analyze_item(
            question_data, correct_answer, total_scores, high_group, low_group
        )
        analysis_results.append(
            {
                "question": col,  # Use the question/column identifier
                **results,
            }
        )

    return analysis_results
