FROM python:3.7
WORKDIR /auto-scaling
COPY ./requirements.txt /auto-scaling/requirements.txt
COPY ./controller /auto-scaling/controller
COPY ./dashboard /auto-scaling/dashboard
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y clean
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
