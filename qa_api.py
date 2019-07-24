import falcon
import json
import spacy
from collections import Counter
nlp = spacy.load("en_core_web_sm")

# Loads Objectives and Modules
with open ('./resource/Objectives.json', 'r') as obj:
  obj = json.load(obj)
with open ('./resource/Modules.json', 'r') as mod:
  mod = json.load(mod)
with open ('./resource/Sprints.json', 'r') as spr:
  spr = json.load(spr)

# Finds word frequencies in given text
# I have given words that are functions like ".map" or ".reduce" a higher weight 2 versus 1 for any other word.
def getFreq (text):
  counts = Counter()
  t = nlp(text)
  for word in t:
    if word.pos_ == "PUNCT" and len(word) > 1:
      counts[word.orth_] += 2
    else:
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

# Creates URLs for data objects
for d in data:
  for s in spr:
    if d["name"].lower().replace(" ","") in s["Modules"].lower().replace(" ",""):
      d.update({"curriculum": s["Curriculum Sets"]})
      if "computerscience" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/cs/module/" + d["record"]})
      elif "ds" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/ds/module/" + d["record"]})
      elif "fullstack" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/fsw/module/" + d["record"]})
      elif "android" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/android/module/" + d["record"]})
      elif "careerreadiness" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/cr/module/" + d["record"]})
      elif "ux" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/ux/module/" + d["record"]})
      elif "ios" in d["curriculum"].lower().replace(" ",""):
        d.update({"URL": "https://learn.lambdaschool.com/ios/module/" + d["record"]})
      elif "principles" in d["curriculum"].lower().replace(" ",""):
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
    question = nlp(req.media["question"].lower())
    doc = [(w.text,w.pos_) for w in question]

    # qwords = a list of key words asked in the question (doc)
    qwords = []
    for w in doc:
      if w[1] != 'DET' and w[1] != 'VERB' and w[1] != 'PRON' and w[1] != 'PART' and w[1] != 'ADV' and w[1] != 'ADP' and w[1] != 'PUNCT':
        qwords.append(w[0])
      if w[1] == 'PUNCT' and len(w[0]) != 1:
        qwords.append(w[0])
    
    matches = []
    for d in data:
      newMatch = {
        "modName": d["name"],
        "data": d,
        "nameMatch": [],
        "textMatch": [],
        "score": 0
      }
      for w in qwords:
        if w in d["name"].lower(): 
          newMatch["nameMatch"].append((w,2))
        if w in d["searchProfile"]["wordFreq"]:
          newMatch["textMatch"].append((w, d["searchProfile"]["wordFreq"][w]))

      if newMatch["score"] == 0 and (newMatch["nameMatch"] != [] or newMatch["textMatch"] != []):
        for nScore in newMatch["nameMatch"]:
          newMatch["score"] += nScore[1]
        for tScore in newMatch["textMatch"]:
          newMatch["score"] += tScore[1]
        matches.append(newMatch)
    
    # this is to cut out matches that do not have a URL and list the ones that do from Highest score to Lowest
    trimMatches = []
    for m in matches:
      if "URL" in m["data"]:
        trimMatches.append(m)
    matches = trimMatches
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    answer = {"matches": matches} 
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