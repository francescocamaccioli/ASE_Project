FROM python:3.12-slim

ADD . /dbm
WORKDIR /dbm

RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
