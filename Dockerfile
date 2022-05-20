FROM ubuntu:latest

LABEL version="0.9"
LABEL maintainer="Ben Krueger <sayhello@blk8.de>"

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-psycopg2

RUN pip3 install flask flask-sqlalchemy flask-login flask-sitemap markdown2 boto3 mkdocs

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/false flask

EXPOSE 5010

USER flask

RUN mkdir /home/flask/templates /home/flask/static /home/flask/uploads /home/flask/downloads /home/flask/.aws

COPY *.py *.sh *.yml /home/flask/
COPY templates/ /home/flask/templates/
COPY static/ /home/flask/static/
COPY docs/ /home/flask/docs/

RUN cd /home/flask && mkdocs build

CMD ["/home/flask/flask.sh"]  
