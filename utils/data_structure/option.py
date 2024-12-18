class Option:
    option_stats = {
        'selected_by': 0, 'top_selected': 0, 'bottom_selected': 0, 'ratio' : 0
    }
    def __init__(self, content):
        self.content = content
        self.option_stats = {
            'selected_by': 0, 
            'top_selected': 0, 
            'bottom_selected': 0, 
            'ratio': 0,
            'discrimination': 0,
            'r_bpis': 0
        }
        self.students = []