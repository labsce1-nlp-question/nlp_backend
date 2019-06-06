import falcon
import csv
import en_core_web_sm
nlp = en_core_web_sm.load()

with open('Objectives-Master List.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter='\n')
    data = []

    for row in readCSV:
        data.append(row)

    # Data is reversed simply so viewable print output in terminal relates to first lines of CSV
    # data.reverse()
    # print(data)

class QA:
    def on_get(self, req, resp):
        """Handles GET requests"""
        welcome = {
            "welcome": "I have the answers..."
        }

        resp.media = welcome
    
    def on_post(self, req, resp):
        """Handles POST requests"""
        doc = nlp(req.media['question'])
        tokens = [(w.text, w.pos_) for w in doc]
        print(tokens)
        
        answer = {'answer' : 'This is the training kit you were looking for.'}
        resp.media = answer


api = falcon.API()
api.add_route('/qa', QA())

# Using Python 3.7
# to install needed tools: `pip3 install gunicorn falcon`
# to run server cd into `qa_api/` and run this command in terminal: `gunicorn --reload -b 0.0.0.0:8000 qa_api:api`
# you may then make calls to: `localhost:8000/qa`
# POST request expects to recieve json = {'question': 'your question'} and returns json = {'answer': 'here is your desired training kit'}
# To install spacy:
# pip3 install -U spacy
# python3 -m spacy download en