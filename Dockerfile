FROM python:3.7
WORKDIR /auto-scaling
COPY ./requirements.txt /auto-scaling/requirements.txt
COPY ./controller /auto-scaling/controller
RUN apt-get update && apt-get upgrade -y && apt-get -y clean
RUN pip install -r requirements.txt
