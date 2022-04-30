FROM ubuntu:latest

LABEL version="0.9"
LABEL maintaner="Ben Krueger <sayhello@blk8.de>"

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-psycopg2

RUN pip3 install flask flask_httpauth flask-sqlalchemy markdown2

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/false flask

EXPOSE 5010

USER flask

RUN mkdir /home/flask/templates /home/flask/static /home/flask/.kringlecon

COPY *.py *.sh /home/flask/
COPY templates/*.html /home/flask/templates/
COPY static/*.css static/*.jpg /home/flask/static/

CMD ["/home/flask/flask.sh"]  
