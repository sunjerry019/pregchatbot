# Custom modules
from custom_classes import datarow, result

# Standard suite
import numpy as np
import csv

# NLP modules
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from autocorrect import spell
from nltk.corpus import wordnet as wn

# Vector comparison module
from sklearn.metrics.pairwise import cosine_similarity



# Core chatbot functions
def load_csv_into_memory(directory, model):
    """ Load dataset into memory. Run once at the start of application.

    Keyword arguments:
    directory -- file directory of .csv file with question-answer pairs

    """

    with open(directory) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        datarows = []
        loaded_vectors = []

        for row in csv_reader:
            try:
                current = datarow(row[0])
                current.answer = row[1]
                current.interrogative = row[2]
                datarows.append(current)

                # Process read-in line
                keyword_list, unprocessed_words, vector = process(row[0], model)
                current.vector = vector

                while 'i' in keyword_list:
                    keyword_list.remove('i')

                if np.isnan(current.vector[0]):
                    print("ZERO VECTOR ALERT")
                    continue

            except:
                print("FAIL")
                traceback.print_exc()
                continue

        print("Datarows loaded: {}".format(len(datarows)))

        return datarows


def query(q, model, datarows, debug = False):
    """ Query the dataset.

    Keyword arguments:
    q -- question object
    debug -- set boolean as True to also print predicted question

    Returns:
    target answer -- predicted answer in string form

    """

    # Process q using engine import
    q.all_keywords, q.unprocessed_keywords, q.vector = process(q.string, model, debug)
    q.vector = np.reshape(q.vector, (1, -1))
    find_interrogative(q)

    q.processed_keywords = [word for word in q.all_keywords if word not in q.unprocessed_keywords]

    print("Final processed keywords:\t{}".format(q.processed_keywords))

    # Iterate through all dataset questions, storing dataset question-similarity pairs in similarity_dict
    similarity_dict = {}
    similarity_list = []
    results = []
    payload = []

    for row in datarows:
        try:
            comparison_sentence_vector = np.reshape(row.vector, (1, -1))
            sim = cosine_similarity(comparison_sentence_vector, q.vector)[0][0]
            results.append(result(row.question, sim, row.interrogative))
            similarity_list.append(sim)
        except:
            print("RUH-ROH")
            print("Subject 1: {}".format(comparison_sentence_vector))
            print("Subject 2: {}".format(q.vector))

    ## DEVSPACE
    similarity_list.sort(reverse=True)
    count = 1

    print('\n')
    print("Input question: {}".format(q.string))

    # No interrogative
    if not q.interrogative:
        print("NO INTERROGATIVE IDENTIFIED")
        # Check for relevant symptom datarow
        i = 0
        num_ans = 0
        while True:
            sim = similarity_list[i]
            if sim < 0.7:
                break

            current_question = sim_to_question(sim, results)
            current_datarow = question_to_datarow(current_question, datarows)
            # Last part of line below is debatable
            if (current_datarow.interrogative == 'symptom' or current_datarow.interrogative == 'what'):
                print("[{:.4f}] Predicted question v1: \t{}".format(sim, current_question))
                payload.append(current_question)
                similarity_list.remove(sim)
                num_ans+=1
            i+=1
        # Relevant datarow not found
        i = 0
        while True:
            sim = similarity_list[i]
            if sim < 0.6:
                break

            current_question = sim_to_question(sim, results)
            current_datarow = question_to_datarow(current_question, datarows)
            print("[{:.4f}] Potential question v2: \t{}".format(sim, current_question))
            payload.append(current_question)
            similarity_list.remove(sim)
            i+=1

    # Have interrogative
    else:
        # Find datarow with correct interrogative
        print("INTERROGATIVE IDENTIFIED: {}".format(q.interrogative))
        i = 0
        while True:
            sim = similarity_list[i]
            if sim < 0.7:
                break
            current_question = sim_to_question(sim, results)
            current_datarow = question_to_datarow(current_question, datarows)
            if current_datarow.interrogative == q.interrogative:
                print("[{:.4f}] Potential question v3: \t{}".format(sim, current_question))
                payload.append(current_question)
                similarity_list.remove(sim)
            i+=1

        # No datarow with correct interrogative found, offer related datarows with strict criteria
        i = 0
        while True:
            sim = similarity_list[i]
            if sim < 0.8:
                break
            current_question = sim_to_question(sim, results)
            current_datarow = question_to_datarow(current_question, datarows)
            print("[{:.4f}] Potential question v4: \t{}".format(sim, current_question))
            payload.append(current_question)
            similarity_list.remove(sim)
            i+=1

        # No datarow with correct interrogative found, offer symptoms
        i = 0
        while True:
            sim = similarity_list[i]
            if sim < 0.5:
                break
            current_question = sim_to_question(sim, results)
            current_datarow = question_to_datarow(current_question, datarows)
            if current_datarow.interrogative == 'symptom':
                print("[{:.4f}] Potential question v5: \t{}".format(sim, current_question))
                payload.append(current_question)
                similarity_list.remove(sim)
            i+=1

    print("SEARCH OVER")
    print("\n")
    return payload


# Supporting chatbot functions
def process(question, model, debug = False):
    """ Processes a string question, identifying keywords and computing its semantic vector.

    Keyword arguments:
    question -- string representation of a question

    Returns:
    keyword_list -- identified keywords in the input question
    semantics_vector -- semantics vector of the input question

    """
    keyword_list = get_lemmatized_keywords(question, debug)
    semantics_vector, unprocessed_words = get_semantics_vector(keyword_list, model, debug)

    return keyword_list, unprocessed_words, semantics_vector


def get_lemmatized_keywords(question, debug = False):
    """ Process a question.

    Keyword arguments:
    question -- question provided in string form

    Returns:
    keyword_list -- list of string keywords
    sentence_vector -- symantic row vector of length 300 representing meaning of the word, created by summing the word vectors
                       of keywords in the question and dividing the result by the number of keywords
    """

    # Tokenize
    tokenized_data = word_tokenize(question)

    # Cast to lower-case
    tokenized_lower = []
    for word in tokenized_data:
        tokenized_lower.append(word.lower())

    # Remove stop words
    tokenized_lower_stopwords = remove_stopwords(tokenized_lower)

    # Spellcheck
    tokenized_lower_stopwords_spellchecked = spellcheck(tokenized_lower_stopwords, debug)

    # Part-of-speech tagging/keyword extraction
    keyword_list = extract_keywords(tokenized_lower_stopwords_spellchecked)

    # Lemmatize
    keyword_list_lemmatized = lemmatize(keyword_list)

    # Cast to US-English
    keyword_list_lemmatized_casted = []
    for word in keyword_list_lemmatized:
        keyword_list_lemmatized_casted.append(uk_to_us(word))

    return keyword_list_lemmatized_casted


def get_semantics_vector(word_list, model, debug = False):
    """ Get semantics vector of a list of words by averaging over the semantics vector of each individual word.

    Keyword arguments:
    word_list -- list of strings to be averaged over

    Returns:
    semantics_vector -- average semantics vector of the input list of strings
    """

    unprocessed_words = []

    semantics_vector = np.zeros(300,)
    word_count = 0
    miscount = 0
    for word in word_list:
        try:
            semantics_vector += model.get_vector(word)
            word_count += 1
        except KeyError:
            if debug:
                miscount += 1
                print("{} word not found in dictionary ({})".format(miscount, word))
                unprocessed_words.append(word)
    if word_count > 0:
        semantics_vector /= word_count

    return semantics_vector, unprocessed_words


def uk_to_us(uk_in):
    with open(r'uk_to_us.csv', mode='r') as infile:
        reader = csv.reader(infile)
        conversion_dict = {rows[0]:rows[1] for rows in reader}

    try:
        us_out = conversion_dict[uk_in]
        return us_out
    except:
        return uk_in


def remove_stopwords(word_list):
    """ Remove stopwords from a list of words.

    Keyword arguments:
    word_list -- list of strings from which stopwords should be removed from

    Returns:
    word_list_out -- list of strings with stopwords removed
    """

    word_list_out = []
    stopWords = set(stopwords.words('english'))

    # Adding custom stopwords
    stopWords.add('pregnant')
    stopWords.add('pregnancy')
    stopWords.remove('more')

    for word in word_list:
        if word not in stopWords:
            word_list_out.append(word)

    return word_list_out


def spellcheck(word_list, debug = False):
    """ Spellcheck a list of words using the autocorrect library.

    Keyword arguments:
    word_list -- list of strings to be spellchecked

    Returns:
    spellchecked_word_list -- list of spellchecked strings
    """

    spellchecked_word_list = []
    for word in word_list:
        spellchecked_word_list.append(spell(word))

    if debug:
        print("Keywords before spellcheck: \t{}".format(word_list))
        print("Keywords after spellcheck: \t{}".format(spellchecked_word_list))

    return spellchecked_word_list


def extract_keywords(word_list):
    """ Extract keywords from a list of strings using their POS tag.

    Keyword arguments:
    word_list -- list of strings to be checked for importance

    Returns:
    keyword_list -- list of keyword strings
    """

    singulars = []
    for word in word_list:
        if len(word) == 1:
            singulars.append(word)

    word_list = [word for word in word_list if word not in singulars]

    tup_list = pos_tag(word_list)
    target_tags = {'NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'JJ', 'JJR', 'JJS', 'WRB', 'MD',
                   'CD', 'RB', 'RBR', 'RBS', 'JJ', 'JJR', 'JJS', 'IN'}
    keyword_list = []

    for tup in tup_list:
        if tup[1] in target_tags:
            keyword_list.append(tup)

    return keyword_list


def lemmatize(word_list):
    """ Lemmatize a list of words using their POS tag if possible.

    Keyword arguments:
    word_list -- list of strings to be lemmatized

    Returns:
    word_list_lemmatized -- list of lemmatized strings
    """

    wordnet_lemmatizer = WordNetLemmatizer()
    word_list_lemmatized = []

    for word in word_list:
        if word[0].isalpha():
            try:
                word_list_lemmatized.append(wordnet_lemmatizer.lemmatize(word[0], pos=penn_to_wn(word[1])))
            except:
                try:
                    word_list_lemmatized.append(wordnet_lemmatizer.lemmatize(word[0]))
                except:
                    pass

    return word_list_lemmatized


def find_interrogative(q):
    interrogative_words = ['who', 'why', 'where', 'what', 'when', 'how', 'can', 'should', 'will', 'do']
    prime_interrogative_words = ['who', 'why', 'where', 'what', 'when', 'how']

    interrogatives_identified = []

    for word in q.string.lower().split():
        if word in interrogative_words:
            interrogatives_identified.append(word)

    interrogatives_identified = ['should' if inter == "can" else inter for inter in interrogatives_identified]

    if len(interrogatives_identified) == 1:
        q.interrogative = interrogatives_identified[0]
        return interrogatives_identified[0]
    elif len(interrogatives_identified) > 1:
        for inter in interrogatives_identified:
            if inter in prime_interrogative_words:
                q.interrogative = inter
                return inter
        q.interrogative = interrogatives_identified[0]
        return interrogatives_identified[0]


def is_noun(tag):
    return tag in ['NN', 'NNS', 'NNP', 'NNPS']


def is_verb(tag):
    return tag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']


def is_adverb(tag):
    return tag in ['RB', 'RBR', 'RBS']


def is_adjective(tag):
    return tag in ['JJ', 'JJR', 'JJS']


def penn_to_wn(tag):
    if is_adjective(tag):
        return wn.ADJ
    elif is_noun(tag):
        return wn.NOUN
    elif is_adverb(tag):
        return wn.ADV
    elif is_verb(tag):
        return wn.VERB
    return None


# Helper lookup functions
def sim_to_question(sim, results):
    for result in results:
        if (abs(sim-result.sim) < 1e-9):
            return result.question
    print("SIMILARITY LOOKUP ERROR")


def question_to_datarow(question, datarows):
    for datarow in datarows:
        if question == datarow.question:
            return datarow
    print("DATAROW LOOKUP ERROR")
