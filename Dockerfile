FROM ubuntu:20.04

LABEL version="0.9"
LABEL maintaner="Ben Krueger <sayhello@blk8.de>"

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-psycopg2

RUN pip3 install flask

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/false flask

EXPOSE 5010

USER flask

RUN mkdir /home/flask/templates /home/flask/.kringlecon

COPY *.py *.sh /home/flask/
COPY templates/*.html /home/flask/templates/

CMD ["/home/flask/flask.sh"]  
