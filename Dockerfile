FROM ubuntu:20.04

LABEL version="0.1"
LABEL maintaner="Ben Krueger <sayhello@blk8.de>"
#LABEL release-date="2020-04-05"
#LABEL promoted="true"

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-psycopg2

RUN pip3 install flask

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

COPY *.py *.sh /root/

EXPOSE 5010

CMD ["/root/flask.sh"]  
