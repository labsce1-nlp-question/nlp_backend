import falcon
import json
import spacy
import requests
import time
from collections import Counter
from dotenv import load_dotenv
import os

# finalT0 = time.time()
load_dotenv()
AIRTABLE_KEY = os.getenv('AIRTABLE_KEY')
nlp = spacy.load("en_core_web_sm")

"""Generates ./tables json data from Airtable:"""
def getAirData():
  print("Start of getAirData--->\n")
  t0 = time.time()
  getAir = True
  if getAir:
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
          for module in m["records"]:
            modules.append(module)
        else:
          print("Error getting offset")
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
      curriculumSets = c["records"]

      while "offset" in c:
        offset = c["offset"]
        response = requests.get(
          f"https://api.airtable.com/v0/app84GmnQ9SxIBjrJ/Curriculum%20Sets?offset={offset}",
          headers = {"Authorization" : f"Bearer {AIRTABLE_KEY}"},
        )
        if response:
          c = response.json()
          for curriculumSet in c["records"]:
            curriculumSets.append(curr)
        else:
          print("Error getting offset", response.text)
    else:
      print("Error getting Curriculum Sets", response.text)
    
    # Make curriculumSets.json
    with open("./tables/curriculumSets.json", "w") as f:
      json.dump(curriculumSets, f)

    getRecord = {}
    for module in modules:
      getRecord[module["id"]] = module
    for objective in objectives:
      getRecord[objective["id"]] = objective
    for curriculumSet in curriculumSets:
      getRecord[curriculumSet["id"]] = curriculumSet

    with open("./tables/getRecord.json", "w") as f:
      json.dump(getRecord, f)
  else:
    return

  speed = time.time() - t0
  print(f"\nSpeed: {speed}")
  print("\n<---End of getAirData")

def genModSearchData():
  print("Start of genModSearchData--->\n")
  t0 = time.time()
  modSearchData = []

  # Loads jsons from ./tables
  with open ('./tables/modules.json', 'r') as modules:
    modules = json.load(modules)
  with open ('./tables/objectives.json', 'r') as objectives:
    objectives = json.load(objectives)
  with open ('./tables/curriculumSets.json', 'r') as curriculumSets:
    curriculumSets = json.load(curriculumSets)
  with open ('./tables/getRecord.json', 'r') as getRecord:
    getRecord = json.load(getRecord)

  # Creates newEntry for modSearchData:
  for module in modules:
    newEntry = {}
    modSearchProfile = {}
    newEntry["id"] = module["id"]
    moduleFields = module["fields"]

    # text is a compilation of relavent search text found in modules fields and objectives fields 
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
          newURL = f"https://learn.lambdaschool.com/{shortID}" + "/module/" + moduleFields["RecordID"]
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
      def getFreq (text):
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
        text = text + moduleFields["Instructors Notes"]

      for objective in linkedObjectives:
        objectiveFields = objective["fields"]

        if "Student can" in objectiveFields:
          text = text + " " + objectiveFields["Student can"]
        if "Description/Rationale" in objectiveFields:
          text = text + " " + objectiveFields["Description/Rationale"]
        if "Introduction" in objectiveFields:
          text = text + " " + objectiveFields["Introduction"]
        if "Tutorial" in objectiveFields:
          text = text + " " + objectiveFields["Tutorial"]
        if "Instructor Notes" in objectiveFields:
          text = text + " " + objectiveFields["Instructor Notes"]
        if "Challenge" in objectiveFields:
          text = text + " " + objectiveFields["Challenge"]
      
      text = text.lower()
      modSearchProfile["text"] = text
      modSearchProfile["textFreq"]= getFreq(text)
      newEntry["modSearchProfile"] = modSearchProfile
      modSearchData.append(newEntry)
  
  with open("./modSearchData.json", "w") as f:
    json.dump(modSearchData, f)
  
  speed = time.time() - t0
  print(f"modSearchData length: {len(modSearchData)} \nSpeed: {speed}")
  print("\n<---End of genModSearchData")

# getAirData()
# genModSearchData()

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
    with open("./modSearchData.json", "r") as modSearchData:
      modSearchData = json.load(modSearchData)

    question = nlp(req.media["question"].lower())
    doc = [(w.text,w.pos_) for w in question]
    # print(f"Question: {question}\nNLP Doc: {doc}")

    # qwords = a list of key words asked in the question (doc)
    qwords = []
    for w in doc:
      if w[1] != 'DET' and w[1] != 'VERB' and w[1] != 'PRON' and w[1] != 'PART' and w[1] != 'ADV' and w[1] != 'ADP' and w[1] != 'PUNCT':
        qwords.append(w[0])
      if w[1] == 'PUNCT' and len(w[0]) != 1:
        qwords.append(w[0])
    
    matches = []
    for module in modSearchData:
      newMatch = {
        "id": module["id"],
        "name": module["name"],
        "description": module["description"],
        "URL": module["URL"],
        "nameMatch": [],
        "textMatch": [],
        "score": 0
      }

      modSearchProfile = module["modSearchProfile"]

      if modSearchProfile["text"] == "NO_TEXT":
        return
      else:  
        for w in qwords:
          if w in newMatch["name"]: 
            newMatch["nameMatch"].append((w,2))
          if w in modSearchProfile["textFreq"]:
            newMatch["textMatch"].append((w, modSearchProfile["textFreq"][w]))

      if newMatch["score"] == 0 and (newMatch["nameMatch"] != [] or newMatch["textMatch"] != []):
        for nScore in newMatch["nameMatch"]:
          newMatch["score"] += nScore[1]
        for tScore in newMatch["textMatch"]:
          newMatch["score"] += tScore[1]
        matches.append(newMatch)
         
    matches.sort(key=lambda x: x["score"], reverse=True)
    resp.media = matches

api = falcon.API()
api.add_route('/qa', QA())

# loadTime = time.time() - finalT0
# print(f"<---QA Ready---> \nLoad Time: {loadTime}")

# To run server cd into `./nlp_backend` and run this command in terminal: `gunicorn --reload --timeout 300 -b 0.0.0.0:8000 qa_api:api`
# you may then make calls to: `localhost:8000/qa`
# POST request expects to recieve json = {'question': 'your question'} and returns an array of matches