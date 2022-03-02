FROM ubuntu:bionic

WORKDIR /webserver

COPY setup_webserver.sh .
COPY requirements.txt .
COPY main.py .

RUN chmod +x ./setup_webserver.sh && ./setup_webserver.sh
RUN pip3 install -r requirements.txt

EXPOSE 2000:2000

CMD python3 main.py
