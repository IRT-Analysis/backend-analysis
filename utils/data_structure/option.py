class Option:
    option_stats = {
        'correct_answer': 0, 'selected_by': 0, 'top_selected': 0, 'bottom_selected': 0, 'ratio' : 0
    }
    def __init__(self, content):
        self.content = content
        self.option_stats = {
            'correct_answer': 0, 
            'selected_by': 0, 
            'top_selected': 0, 
            'bottom_selected': 0, 
            'ratio': 0
        }