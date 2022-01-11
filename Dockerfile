FROM python:slim-buster

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY deamon.py /app/

ENTRYPOINT ["python", "deamon.py"]