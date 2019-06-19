import falcon
import json
import en_core_web_sm
from collections import Counter
nlp = en_core_web_sm.load()

# Loads Objectives and Modules
with open ('Objectives.json', 'r') as obj:
  obj = json.load(obj)
with open ('Modules.json', 'r') as mod:
  mod = json.load(mod)
with open ('Sprints.json', 'r') as spr:
  spr = json.load(spr)

# Finds word frequencies in given text
def getFreq (text):
  counts = Counter()
  t = nlp(text)
  for word in t:
    counts[word.orth_] += 1
  return counts

# Builds Data by matching Objectives and Modules as well as adding information to make search easier
data = []
for o in obj:
  for m in mod:
    if o["Modules"].lower().replace(" ", "") == m["Name"].lower().replace(" ", "") and o["Modules"] != "" and m["Name"] != "":
      t = (o["Student can"] + " " + m["Description"] + " " + m["Objectives"]).lower()
      data.append({
        "name": m["Name"],
        "record": m["RecordID"],
        "objective": o, 
        "module": m,
        "searchProfile": {
          "text": t,
          "wordFreq": getFreq(t)
        }
      })

for d in data:
  for s in spr:
    if d["name"].lower().replace(" ","") in s["Modules"].lower().replace(" ",""):
      d.update({"curriculum": s["Curriculum Sets"]})
      if "computerscience" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/cs/module/" + d["record"]})
      if "ds" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/ds/module/" + d["record"]})
      if "fullstack" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/fsw/module/" + d["record"]})
      if "android" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/android/module/" + d["record"]})
      if "careerreadiness" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/cr/module/" + d["record"]})
      if "ux" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/ux/module/" + d["record"]})
      if "ios" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/ios/module/" + d["record"]})
      if "principles" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/p4s/module/" + d["record"]})

# lostSouls is made up of unmatchable objectives and modules...
lostSouls = []
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
    question = nlp(req.media['question'].lower())

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
#   pip3 install -U spacy
#   python3 -m spacy download en