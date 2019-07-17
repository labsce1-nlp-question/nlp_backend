FROM python

WORKDIR /app

RUN apt update -y &&\
    apt install -y build-essential python-dev

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN pip install gunicorn[gevent]

RUN python3 -m spacy download en

COPY . .

EXPOSE 8000

WORKDIR /app/qa_api

ENTRYPOINT [ "gunicorn" ]

CMD [ "--reload", "--timeout 120", "-b 0.0.0.0:8000", "--workers 2", "--worker-class gevent", "qa_api:api" ]

# RUN "gunicorn --reload --timeout 120 -b 0.0.0.0:8000 --workers 2 --worker-class gevent qa_api:api"

# CMD [ "gunicorn", "--reload --timeout 120 -b 0.0.0.0:8000", "qa_api:api"]
# CMD [ "gunicorn", "--reload", "--timeout 120", "-b 0.0.0.0:8000", "qa_api:api"]