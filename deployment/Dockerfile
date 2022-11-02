FROM python:3.8-slim-buster

RUN apt-get update -y && apt-get install -y python3-pip

WORKDIR /root/.kube/

COPY deployment/config/config config

WORKDIR /app-aware-nsm

COPY apis/ apis/
COPY core/ core/
COPY app.py app.py
COPY setup.py setup.py
COPY deployment/config/config.ini config.ini
COPY deployment/config/locations.yaml locations.yaml
COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]