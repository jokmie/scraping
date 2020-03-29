
FROM python:3.7-slim
#FROM gcr.io/google-appengine/python
    
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /
CMD [ "python", "main.py"]