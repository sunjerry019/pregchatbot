# Custom modules
from custom_functions import load_csv_into_memory

# Word embedding module
import gensim
import time
import traceback
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')



# Load pre-trained word embeddings
start_time = time.clock()
model = gensim.models.KeyedVectors.load_word2vec_format(r"GoogleNews-vectors-negative300.bin.gz", limit=10000, binary=True)
end_time = time.clock()
print('Embeddings successfully loaded!')
print('Time elapsed:', end_time - start_time, 'seconds')

# Load csv into memory
datarows = load_csv_into_memory(r"labeled-database.csv", model)



#v1: no interrogative, have relevant SYMPTOM or WHAT QUESTION
#v2: no interrogative, have relevant CONTENT
#v3: have interrogative, correct interrogative found
#v4: have interrogative, no correct interrogative found but have strictly relevant datarow
#v5: have interrogative, no correct interrogative found but have relevant SYMPTOM


#input_qn = question("stomach pain")
#print("Predicted answer: {}".format(query(input_qn, debug=True)))

