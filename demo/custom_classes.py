class question:
    def __init__(self, string):
        self.string = string
        self.all_keywords = None
        self.unprocessed_keywords = None
        self.processed_keywords = None
        self.interrogative = None
        self.vector = None
        
class datarow:
    def __init__(self, question):
        self.question = question
        self.answer = None
        self.interrogative = None
        self.vector = None
        
class result:
    def __init__(self, question, sim, interrogative):
        self.question = question
        self.sim = sim
        self.interrogative = interrogative


