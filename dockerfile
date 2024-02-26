FROM python:3.7
WORKDIR python-aas-registry
COPY . .

RUN pip3 install APScheduler python-snap7 werkzeug Flask Flask-RESTful python-dotenv requests jsonschema aiocoap hbmqtt

CMD [ "python3","-u", "./src/main/vws_ric.py" ]

ENV TZ=Europe/Berlin
