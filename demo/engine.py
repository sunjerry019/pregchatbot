# Custom modules
from custom_functions import load_csv_into_memory, query
from custom_classes import question

# Word embedding module
import gensim
import time
import traceback
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

# SMTP imports
import smtplib, ssl
from getpass import getpass


#v1: no interrogative, have relevant SYMPTOM or WHAT QUESTION
#v2: no interrogative, have relevant CONTENT
#v3: have interrogative, correct interrogative found
#v4: have interrogative, no correct interrogative found but have strictly relevant datarow
#v5: have interrogative, no correct interrogative found but have relevant SYMPTOM


#input_qn = question("stomach pain")
#print("Predicted answer: {}".format(query(input_qn, debug=True)))


class engine:
    def __init__(self):
        self.model = self.load_vectors()
        self.datarows = load_csv_into_memory(r"labeled-database.csv", model)

        self.port = 465  # For SSL
        self.password = '420blazeit!'
        self.sender_email = "chatbotquestionbank420@gmail.com"
        self.receiver_email = "chatbotquestionbank420@gmail.com"

    def load_vectors(self):
        # Load pre-trained word embeddings
        start_time = time.clock()
        model = gensim.models.KeyedVectors.load_word2vec_format(r"GoogleNews-vectors-negative300.bin.gz", limit=10000, binary=True)
        end_time = time.clock()
        
        print('Embeddings successfully loaded!')
        print('Time elapsed:', end_time - start_time, 'seconds')
        
        return model

    def ask(q):
        input_qn = question(q)
        payload = query(input_qn, self.model, self.datarows, debug=True)
        print("Question:{}".format(q))

        return payload

    # Function to send email with missing question as message
    def add_to_questionbank(message):
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login("chatbotquestionbank420@gmail.com", password)
            server.sendmail(sender_email, receiver_email, message)

