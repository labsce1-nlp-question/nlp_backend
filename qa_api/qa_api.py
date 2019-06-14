import falcon
import json
import en_core_web_sm
nlp = en_core_web_sm.load()

# Loads Objectives and Modules
with open ('Objectives.json', 'r') as obj:
  obj = json.load(obj)
with open ('Modules.json', 'r') as mod:
  mod = json.load(mod)

# data is made up of Objective:Module pairs
data = {}
# lostSouls is made up of unmatchable objectives and modules...
lostSouls = []

# Builds Data
for o in obj:
  for m in mod:
    if o["Modules"] == m["Name"] and o["Modules"] != "" and m["Name"] != "":
      data[m["Name"]] = {"objective": o, "module": m}

# Harvests Souls
for o in obj:
  if o["Modules"] == "":
    lostSouls.append(o)
for m in mod:
  if m["Name"] == "":
    lostSouls.append(m)

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
    answer = data
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