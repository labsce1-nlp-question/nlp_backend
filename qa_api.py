# To run server cd into `./nlp_backend` and run this command in terminal:
# `gunicorn --reload --timeout 600 -b 0.0.0.0:8000 qa_api:api`
# you may then make calls to: `localhost:8000/qa`
# POST request expects to recieve json = {'question': 'your question'}
# and returns an array of matches

import falcon
import json
import spacy
import requests
import time
from collections import Counter
from dotenv import load_dotenv
import os
import pandas as pd
import subprocess
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string
import random

# NLTK related imports
import nltk
from nltk.tokenize import word_tokenize  # Word Tokenizer
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer  # Word Lemmatizer

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

table = str.maketrans('', '', string.punctuation)
stop_words = stopwords.words('english')
stop_words = set(stop_words)

lemmatizer = WordNetLemmatizer()

load_dotenv()
AIRTABLE_KEY = os.getenv('AIRTABLE_KEY')
DEBUG_MODE = os.getenv('DEBUG_MODE')

if DEBUG_MODE == 'ON':
    finalT0 = time.time()

nlp = spacy.load("en_core_web_sm")


def get_jaccard_sim(str1, str2):
    """
    Jaccard similarity:
    Also called intersection over union is defined as size of intersection
    divided by size of union of two sets.
    """
    a = set(str1.split())
    b = set(str2.split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


def get_cosine_sim(*strs):
    """
    Cosine similarity:
    Calculates similarity by measuring the cosine of angle between two vectors.
    """
    vectors = [t for t in get_vectors(*strs)]
    return cosine_similarity(vectors)[0][1]


def get_vectors(*strs):
    text = [t for t in strs]
    vectorizer = CountVectorizer(text)
    vectorizer.fit(text)
    return vectorizer.transform(text).toarray()


def clean_text(text):
    """
    Cleaning the document before vectorization.
    """
    # Tokenize by word
    tokens = word_tokenize(text)
    # Make all words lowercase
    lowercase_tokens = [w.lower() for w in tokens]
    # Strip punctuation from within words
    no_punctuation = [x.translate(table) for x in lowercase_tokens]
    # Remove words that aren't alphabetic
    alphabetic = [word for word in no_punctuation if word.isalpha()]
    # Remove stopwords
    no_stop_words = [w for w in alphabetic if not w in stop_words]  # noqa E713
    # Lemmatize words
    lemmas = [lemmatizer.lemmatize(word) for word in no_stop_words]
    return ' '.join(lemmas)


def getAirData():
    """Generates ./tables json data from Airtable:"""
    if DEBUG_MODE == 'ON':
        print("Start of getAirData--->\n")
        t0 = time.time()

    # Obtain all Modules:
    url = "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Modules"
    auth_value = 'Bearer '+AIRTABLE_KEY
    headers = {"Authorization": auth_value}
    response = requests.get(url, headers=headers,)

    if response:
        m = response.json()
        modules = m["records"]

        while "offset" in m:
            offset = m["offset"]

            url = "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/"\
                  "Modules?offset="+offset  # noqa E999
            auth_value = "Bearer "+AIRTABLE_KEY
            headers = {"Authorization": auth_value}
            response = requests.get(url, headers=headers,)

            if response:
                m = response.json()
                for module in m["records"]:
                    modules.append(module)
            else:
                print("Error getting offset")
    else:
        print("Error getting modules")

    # Make modules.json
    with open("./tables/modules.json", "w") as f:
        json.dump(modules, f, indent=4)

    # Obtain all Objectives:
    url = "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Objectives"
    auth_value = "Bearer "+AIRTABLE_KEY
    headers = {"Authorization": auth_value}
    response = requests.get(url, headers=headers,)

    if response:
        o = response.json()
        objectives = o["records"]

        while "offset" in o:
            offset = o["offset"]

            url = "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/"\
                  "Objectives?offset="+offset
            auth_value = "Bearer "+AIRTABLE_KEY
            headers = {"Authorization": auth_value}
            response = requests.get(url, headers=headers,)

            if response:
                o = response.json()

                for obj in o["records"]:
                    objectives.append(obj)
            else:
                print("Error getting offset")
    else:
        print("Error getting objectives")

    # Make objectives.json
    with open("./tables/objectives.json", "w") as f:
        json.dump(objectives, f, indent=4)

    # Obtain all Currriculum Sets:
    url = "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Curriculum%20Sets"
    auth_value = "Bearer "+AIRTABLE_KEY
    headers = {"Authorization": auth_value}
    response = requests.get(url, headers=headers,)

    if response:
        c = response.json()
        curriculumSets = c["records"]

        while "offset" in c:
            offset = c["offset"]

            url = "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/"\
                "Curriculum%20Sets?offset="+offset
            auth_value = "Bearer "+AIRTABLE_KEY
            headers = {"Authorization": auth_value}
            response = requests.get(url, headers=headers,)

            if response:
                c = response.json()

                for curriculumSet in c["records"]:
                    curriculumSets.append(curriculumSet)
            else:
                print("Error getting offset", response.text)
    else:
        print("Error getting Curriculum Sets", response.text)

    # Make curriculumSets.json
    with open("./tables/curriculumSets.json", "w") as f:
        json.dump(curriculumSets, f, indent=4)

    getRecord = {}
    for module in modules:
        getRecord[module["id"]] = module

    for objective in objectives:
        getRecord[objective["id"]] = objective

    for curriculumSet in curriculumSets:
        getRecord[curriculumSet["id"]] = curriculumSet

    with open("./tables/getRecord.json", "w") as f:
        json.dump(getRecord, f, indent=4)

    if DEBUG_MODE == 'ON':
        speed = time.time() - t0
        print("Speed: "+str(speed))
        print("\n<---End of getAirData")


def genModSearchData():
    """Generates modSearchData.json"""

    if DEBUG_MODE == 'ON':
        print("Start of genModSearchData--->\n")
        t0 = time.time()

    modSearchData = []

    # Loads jsons from ./tables
    with open('./tables/modules.json', 'r') as modules:
        modules = json.load(modules)

    with open('./tables/objectives.json', 'r') as objectives:
        objectives = json.load(objectives)

    with open('./tables/curriculumSets.json', 'r') as curriculumSets:
        curriculumSets = json.load(curriculumSets)

    with open('./tables/getRecord.json', 'r') as getRecord:
        getRecord = json.load(getRecord)

    # Creates newEntry for modSearchData:
    for module in modules:
        newEntry = {}
        modSearchProfile = {}
        newEntry["id"] = module["id"]
        moduleFields = module["fields"]

        # text is a compilation of relavent search text found
        # in modules fields and objectives fields
        text = ""

        if "Name" in moduleFields:
            newEntry["name"] = moduleFields["Name"]
        else:
            newEntry["name"] = "GHOST"

        if "Description" in moduleFields:
            newEntry["description"] = moduleFields["Description"]
            text = text + moduleFields["Description"]
        else:
            newEntry["description"] = "NO_DESCRIPTION"

        # Generates newEntry["URL"]
        # Uses Curriculum Sets Short ID field to complete module URL's:
        newCurriculumSets = []
        noCurriculum = []
        noShortID = []

        if "Curriculum Sets" in moduleFields:
            for curriculumSet in moduleFields["Curriculum Sets"]:
                newCurriculumSets.append(getRecord[curriculumSet])

            for curriculumSet in newCurriculumSets:
                if "Short ID" in curriculumSet["fields"]:
                    shortID = curriculumSet["fields"]["Short ID"].lower()
                    newURL = "https://learn.lambdaschool.com/"+shortID
                    newURL += "/module/" + moduleFields["RecordID"]
                    response = requests.get(newURL)

                    if response:
                        newEntry["URL"] = newURL
                    else:
                        break
                else:
                    noShortID.append(module)
        else:
            noCurriculum.append(module)

        if "URL" in newEntry:
            # Creates newEntry["modSearchProfile"]
            def getFreq(text):
                counts = Counter()
                t = nlp(text)
                for word in t:
                    if word.pos_ == "PUNCT" and len(word) > 1:
                        counts[word.orth_] += 2
                    else:
                        counts[word.orth_] += 1

                return counts

            # Gathers objectives linked to module:
            linkedObjectives = []
            if "Objectives" in moduleFields:
                for objective in moduleFields["Objectives"]:
                    linkedObjectives.append(getRecord[objective])

            # Generates text from objectives
            if "Instructors Notes" in moduleFields:
                text += moduleFields["Instructors Notes"]

            for objective in linkedObjectives:
                objectiveFields = objective["fields"]

                if "Student can" in objectiveFields:
                    text += " " + objectiveFields["Student can"]
                if "Description/Rationale" in objectiveFields:
                    text += " " + objectiveFields["Description/Rationale"]
                if "Introduction" in objectiveFields:
                    text += " " + objectiveFields["Introduction"]
                if "Tutorial" in objectiveFields:
                    text += " " + objectiveFields["Tutorial"]
                if "Instructor Notes" in objectiveFields:
                    text += " " + objectiveFields["Instructor Notes"]
                if "Challenge" in objectiveFields:
                    text += " " + objectiveFields["Challenge"]

            text = text.lower()
            modSearchProfile["text"] = text
            modSearchProfile["textFreq"] = getFreq(text)
            newEntry["modSearchProfile"] = modSearchProfile
            modSearchData.append(newEntry)

    with open("./modSearchData.json", "w") as f:
        json.dump(modSearchData, f, indent=4)

    if DEBUG_MODE == 'ON':
        speed = time.time() - t0
        print("modSearchData length: "+str(len(modSearchData)))
        print("Speed: "+str(speed))
        print("\n<---End of genModSearchData")

    # Reload data after updating modSearchData.json file
    load_data()


def load_data():
    """Loading function before 1st query"""
    print("Data loading started..............................................")
    global available_category
    global df

    # Loading data onto dataframe
    df = pd.read_json('modSearchData.json')

    # Dropping NaN values
    if df.isnull().sum().sum():
        df.dropna(inplace=True)

    # Categorizing the training kit information
    category = []

    cmd = """cat "modSearchData.json" | grep '"URL"' | cut -d/ -f4"""
    section_names = subprocess.check_output(cmd, shell=True)\
        .decode("utf-8").split()

    for section in section_names:
        if section in ['and-pre', 'android']:
            category.append('android')
        elif section in ['cd', 'cr', 'ls-edu', 'nxt', 'p4s']:
            category.append('career')
        elif section in ['cs']:
            category.append('cs')
        elif section in ['ds', 'ds-pre']:
            category.append('ds')
        elif section in ['fsw', 'fsw-pre', 'web1', 'web2',
                         'web3', 'web4java', 'web4node']:
            category.append('web')
        elif section in ['ios', 'ios-pre']:
            category.append('ios')
        elif section in ['ux', 'ux-pre']:
            category.append('ux')
        else:
            category.append('other')

    df['category'] = category

    # Extract text information from modSearchProfile
    def extract_text(row):
        return dict(row)['text']

    df['modSearchText'] = df['modSearchProfile'].apply(extract_text)

    # Combining text based information
    df['text'] = df.apply(lambda row: row['name'] + " " + row['description']
                          + " " + row['modSearchText'], axis=1)

    # Dropping detailed text information.
    # This can be used later if needed.
    df.drop(columns=['modSearchProfile'], inplace=True)

    # Clean up the text
    df['cleaned_text'] = df.text.apply(clean_text)

    # Used for category based search
    available_category = df.category.unique()
    print("Data loading complete.............................................")


def build_response(df, match_type, similarity_metrics, match_count=3):
    """Populates the records to be returned in response."""
    # Dictionary to build response packet
    resp_dict = {}

    # Building the response
    resp_dict['match_type'] = match_type
    resp_dict['similarity_metrics'] = similarity_metrics

    match = []
    for i in range(min(df.shape[0], match_count)):
        row = df.iloc[i, :]

        record = {}
        record['id'] = row['id']
        record['name'] = row['name']
        record['description'] = row['description']
        record['URL'] = row['URL']
        match.append(record)

    resp_dict['match'] = match
    # return json.dumps(resp_dict)
    return resp_dict


# Initializing empty globals
df = pd.DataFrame()
available_category = []

# Need to ensure data is loaded at init for content based search
load_data()


class QA:

    def on_get(self, req, resp):
        """Handles GET requests"""
        with open("./modSearchData.json", "r") as modSearchData:
            modSearchData = json.load(modSearchData)

        if modSearchData:
            resp.media = modSearchData
        else:
            resp.media = {"Error": "No modSearchData"}

    def on_post(self, req, resp):
        """Handles POST requests"""
        global available_category
        global df

        # User Input
        student_query = req.media["question"]

        # Using choice to decide Jaccard or Cosine similarity metrics.
        # Based on choice we design of A/B testing.
        choice = random.randint(0, 1)

        # Check if the category is available
        query_category = student_query.split(":")[0]

        if query_category in available_category:
            df_match_by_category = df[df['category'] == query_category].copy()

            query_without_category = \
                clean_text(student_query.replace(query_category+":", ""))

            df_match_by_category['jaccard_sim_value'] = \
                df_match_by_category.cleaned_text.\
                apply(get_jaccard_sim, args=(query_without_category,))
            sort_by_jaccard_sim = \
                df_match_by_category.sort_values('jaccard_sim_value',
                                                 ascending=False).head(10)
            jaccard_match = sort_by_jaccard_sim[
                                sort_by_jaccard_sim['jaccard_sim_value'] > 0]

            df_match_by_category['cosine_sim_value'] = \
                df_match_by_category.cleaned_text.\
                apply(get_cosine_sim, args=(query_without_category,))
            sort_by_cosine_sim = \
                df_match_by_category.sort_values('cosine_sim_value',
                                                 ascending=False).head(10)

            cosine_match = sort_by_cosine_sim[
                               sort_by_cosine_sim['cosine_sim_value'] > 0]

            # Building the response
            if choice == 0:
                # Using Jaccard similarity metrics
                resp.media = build_response(jaccard_match,
                                            'category search', 'jaccard')
                return
            else:
                # Using Cosine similarity metrics
                resp.media = build_response(cosine_match,
                                            'category search', 'cosine')
                return

        else:
            df_full_match = df.copy()

            df_full_match['jaccard_sim_value'] = \
                df_full_match.cleaned_text.\
                apply(get_jaccard_sim, args=(clean_text(student_query),))
            sort_by_jaccard_sim = \
                df_full_match.sort_values('jaccard_sim_value',
                                          ascending=False).head(10)
            jaccard_match = sort_by_jaccard_sim[
                                sort_by_jaccard_sim['jaccard_sim_value'] > 0]

            df_full_match['cosine_sim_value'] = \
                df_full_match.cleaned_text.\
                apply(get_cosine_sim, args=(clean_text(student_query),))

            sort_by_cosine_sim = \
                df_full_match.sort_values('cosine_sim_value',
                                          ascending=False).head(10)
            cosine_match = sort_by_cosine_sim[
                               sort_by_cosine_sim['cosine_sim_value'] > 0]

            # Building the response
            if choice == 0:
                # Using Jaccard similarity metrics
                resp.media = build_response(jaccard_match,
                                            'full search', 'jaccard')
                return
            else:
                # Using Cosine similarity metrics
                resp.media = build_response(cosine_match,
                                            'full search', 'cosine')
                return


class UpdateQA:

    def on_post(self, req, resp):
        updates = req.media

        if DEBUG_MODE == "ON":
            print("Updates : ", updates)

            # Example:
            # This updates object triggers the creation/update of modSearchData
            # updates = {
            #   "airData": 0,
            #   "modSearchData": 1
            # }
            # updates is an object with keys of the update to make and
            # a value of 1 in order to update and a value of of 0 to not

        if updates["airData"]:
            getAirData()
            resp.media = {"message": "Success updating airData"}
        if updates["modSearchData"]:
            genModSearchData()
            resp.media = {"message": "Success updating modSearchData"}


api = falcon.API()
api.add_route('/qa', QA())
api.add_route('/update', UpdateQA())

if DEBUG_MODE == "ON":
    loadTime = time.time() - finalT0
    print("<---QA Ready---> \nLoad Time: "+str(loadTime))
