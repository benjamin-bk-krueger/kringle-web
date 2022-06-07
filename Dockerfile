FROM ubuntu:22.04

LABEL version="0.9"
LABEL maintainer="Ben Krueger <sayhello@blk8.de>"

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-psycopg2

RUN pip3 install flask flask-sqlalchemy flask-login Flask-WTF email_validator flask_wtf flask-sitemap Flask-Mail flask-restx flask-marshmallow marshmallow-sqlalchemy markdown2 boto3 mkdocs

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/false kringle

EXPOSE 5010

USER kringle

RUN mkdir /home/kringle/templates /home/kringle/static /home/kringle/uploads /home/kringle/downloads /home/kringle/.aws

COPY *.py *.sh *.yml /home/kringle/
COPY templates/ /home/kringle/templates/
COPY static/ /home/kringle/static/
COPY docs/ /home/kringle/docs/

RUN cd /home/kringle && mkdocs build

CMD ["/home/kringle/flask.sh"]  
