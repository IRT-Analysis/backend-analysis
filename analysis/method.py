
class Method:
    def get_score_list(self, scores):
        score_list = [s["score"] for s in scores]
        return score_list

    def get_result_list(self, name, dict):
        list = []
        for key, value in dict.items():
            index = value[name]
            list.append(index)
        return list

    