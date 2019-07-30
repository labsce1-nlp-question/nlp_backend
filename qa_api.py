import falcon
import json
import spacy
import requests
import time
from collections import Counter
from dotenv import load_dotenv
import os

load_dotenv()
AIRTABLE_KEY = os.getenv('AIRTABLE_KEY')
nlp = spacy.load("en_core_web_sm")
data = []

# Generates Data Daily from Airtable:
def dataIntake():
  t0 = time.time()
  global data

  # Set genJsons = True to generate jsons from Airtable tables
  genJsons = False
  while(genJsons):
    # Obtain all Modules:
    response = requests.get(
      "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Modules",
      headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
    )

    if response:
      m = response.json()
      modules = m["records"]

      while "offset" in m:
        offset = m["offset"]
        response = requests.get(
          f"https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Modules?offset={offset}",
          headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
        )
        if response:
          m = response.json()
          for mod in m["records"]:
            modules.append(mod)
        else:
          print("Error getting offset")
      # print(json.dumps(modules, indent=4), len(modules))
    else:
      print("Error getting modules")
    
    # Make modules.json
    with open("./tables/modules.json", "w") as f:
      json.dump(modules, f)

    # Obtain all Objectives:
    response = requests.get(
      "https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Objectives",
      headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
    )

    if response:
      o = response.json()
      objectives = o["records"]

      while "offset" in o:
        offset = o["offset"]
        response = requests.get(
          f"https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Objectives?offset={offset}",
          headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
        )
        if response:
          o = response.json()
          for obj in o["records"]:
            objectives.append(obj)
        else:
          print("Error getting offset")
      # print(json.dumps(objectives, indent=4), len(objectives))
    else:
      print("Error getting objectives")
    
    # Make objectives.json
    with open("./tables/objectives.json", "w") as f:
      json.dump(objectives, f)
    
    # Obtain all Currriculum Sets:
    response = requests.get("https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Curriculum%20Sets",
      headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
    )

    if response:
      c = response.json()
      curriculum = c["records"]

      while "offset" in c:
        offset = c["offset"]
        response = requests.get(
          f"https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Curriculum%20Sets?offset={offset}",
          headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
        )
        if response:
          c = response.json()
          for curr in c["records"]:
            curriculum.append(curr)
        else:
          print("Error getting offset", response.text)
      # print(json.dumps(curriculum, indent=4), len(curriculum))
    else:
      print("Error getting Curriculum", response.text)
    
    # Make curriculumSets.json
    with open("./tables/curriculumSets.json", "w") as f:
      json.dump(curriculum, f)

    # Obtain all Courses:
    response = requests.get("https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/courses",
      headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
    )

    if response:
      c = response.json()
      courses = c["records"]

      while "offset" in c:
        offset = c["offset"]
        response = requests.get(
          f"https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/courses?offset={offset}",
          headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
        )
        if response:
          c = response.json()
          for course in c["records"]:
            courses.append(course)
        else:
          print("Error getting offset", response.text)
      # print(json.dumps(courses, indent=4), "HERE: ", len(courses))
    else:
      print("Error getting Courses", response.text)
    
    # Make courses.json
    with open("./tables/courses.json", "w") as f:
      json.dump(courses, f)

    # Generates a hasth table for easy record look up
    hobj = {}
    hmod = {}
    hcurr = {}
    hcourse = {}
    for obj in objectives:
      hobj[obj["id"]] = obj
    for mod in modules:
      hmod[mod["id"]] = mod
    for curr in curriculum:
      hcurr[curr["id"]] = curr
    for course in courses:
      hcourse[course["id"]] = course
    
    htable = dict(hobj, **hmod, **hcurr, **hcourse)

    # Makes htable.json
    with open("./tables/htable.json", "w") as f:
      json.dump(htable, f)
    genJsons = False
  
  # Loads jsons
  with open ('./tables/modules.json', 'r') as modules:
    modules = json.load(modules)
  with open ('./tables/objectives.json', 'r') as objectives:
    objectives = json.load(objectives)
  with open ('./tables/curriculumSets.json', 'r') as curriculum:
    curriculum = json.load(curriculum)
  with open ('./tables/courses.json', 'r') as courses:
    courses = json.load(courses)
  with open ('./tables/htable.json', 'r') as htable:
    htable = json.load(htable)

  # Set genData = True to generate data
  genData = False
  while(genData):
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

    for mod in modules:
      newEntry = {}
      newEntry["module"] = mod

      newObj = []
      if "Objectives" in mod["fields"]:
        for obj in mod["fields"]["Objectives"]:
          newObj.append(htable[obj])
        newEntry["module"]["fields"]["Objectives"] = newObj

      if "Name" in mod["fields"]:
        newEntry["modName"] = mod["fields"]["Name"]
      else:
        newEntry["modName"] = "GHOST"
      newEntry["modRecord"] = mod["id"]


      if "Description" in mod["fields"]:
        newEntry["description"] = mod["fields"]["Description"]
      else:
        newEntry["description"] = "No Description"

      newCurrSets = []
      noCurrListed = []
      noShortID = []
      if "Curriculum Sets" in  mod["fields"]:
        for currset in mod["fields"]["Curriculum Sets"]:
          newCurrSets.append(htable[currset])
        mod["fields"]["Curriculum Sets"] = newCurrSets

        for currset in mod["fields"]["Curriculum Sets"]:
          if "Short ID" in currset["fields"]:
            shortID = currset["fields"]["Short ID"].lower()
            newURL = f"https://learn.lambdaschool.com/{shortID}" + "/module/" + mod["fields"]["RecordID"]
            response = requests.get(newURL)
            if response:
              newEntry["URL"] = newURL
            else:
              print(response)
          else:
            noShortID.append(mod)
      else:
        noCurrListed.append(mod)
      
      data.append(newEntry)
    
    newData = []
    lostData = []
    for entry in data:
      if "URL" in entry:
        newData.append(entry)
      else:
        lostData.append(entry)

    data = newData
    
    with open('./data.json', 'w') as f:
      json.dump(data, f)
    genData = False

  # Loads data
  with open('./data.json', 'r') as data:
    data = json.load(data)

  speed = time.time() - t0
  print(f"---data length: {len(data)} \n---speed: {speed}")
dataIntake()
print("End of Intake")

# # Builds Data by matching Objectives and Modules as well as adding information to make search easier
# data = []
# for o in obj:
#   for m in mod:
#     if o["Modules"].lower().replace(" ", "") == m["Name"].lower().replace(" ", "") and o["Modules"] != "" and m["Name"] != "":
#       t = (o["Student can"] + " " + m["Description"] + " " + m["Objectives"]).lower()
#       data.append({
#         "name": m["Name"],
#         "record": m["RecordID"],
#         "objective": o, 
#         "module": m,
#         "searchProfile": {
#           "text": t,
#           "wordFreq": getFreq(t)
#         }
#       })

class QA:
  def on_get(self, req, resp):
    """Handles GET requests"""
    welcome = {
      "welcome": "I have the answers..."
    }

    resp.media = data
    
  def on_post(self, req, resp):
    """Handles POST requests"""
    # question = nlp(req.media["question"].lower())
    # doc = [(w.text,w.pos_) for w in question]

    # # qwords = a list of key words asked in the question (doc)
    # qwords = []
    # for w in doc:
    #   if w[1] != 'DET' and w[1] != 'VERB' and w[1] != 'PRON' and w[1] != 'PART' and w[1] != 'ADV' and w[1] != 'ADP' and w[1] != 'PUNCT':
    #     qwords.append(w[0])
    #   if w[1] == 'PUNCT' and len(w[0]) != 1:
    #     qwords.append(w[0])
    
    # matches = []
    # for d in data:
    #   newMatch = {
    #     "modName": d["name"],
    #     "data": d,
    #     "nameMatch": [],
    #     "textMatch": [],
    #     "score": 0
    #   }
    #   for w in qwords:
    #     if w in d["name"].lower(): 
    #       newMatch["nameMatch"].append((w,2))
    #     if w in d["searchProfile"]["wordFreq"]:
    #       newMatch["textMatch"].append((w, d["searchProfile"]["wordFreq"][w]))

    #   if newMatch["score"] == 0 and (newMatch["nameMatch"] != [] or newMatch["textMatch"] != []):
    #     for nScore in newMatch["nameMatch"]:
    #       newMatch["score"] += nScore[1]
    #     for tScore in newMatch["textMatch"]:
    #       newMatch["score"] += tScore[1]
    #     matches.append(newMatch)
    
    # # this is to cut out matches that do not have a URL and list the ones that do from Highest score to Lowest
    # trimMatches = []
    # for m in matches:
    #   if "URL" in m["data"]:
    #     trimMatches.append(m)
    # matches = trimMatches
    # matches.sort(key=lambda x: x["score"], reverse=True)
    
    # answer = {"matches": matches} 
    resp.media = data

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