FROM python:3.8-slim-buster

RUN apt-get update -y && apt-get install -y python3-pip

RUN mkdir /root/.kube/

WORKDIR /app-aware-nsm

COPY apis/ apis/
COPY core/ core/
COPY app.py app.py
COPY setup.py setup.py
COPY deployment/config/config.ini config.ini
COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 5000

RUN apt update && apt install inetutils-ping curl -y

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]