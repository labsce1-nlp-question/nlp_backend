import falcon
import csv

with open('Objectives-Master List.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter='\n')
    
    data = []
    for row in readCSV:
        data.append(row)

    # Data is reversed simply so viewable print output in terminal relates to first lines of CSV
    data.reverse()
    print(data)

class QA:
    def on_get(self, req, resp):
        """Handles GET requests"""
        welcome = {
            "welcome": "I have the answers..."
        }

        resp.media = welcome
    
    def on_post(self, req, resp):
        """Handles POST requests"""
        

api = falcon.API()
api.add_route('/qa', QA())

# Using Python 3.7
# to install needed tools: `pip3 install gunicorn falcon`
# to run server cd into `qa_api/` and run this command in terminal: `gunicorn --reload -b 0.0.0.0:8000 qa_api:api`
# you may then make calls to: `localhost:8000/qa`