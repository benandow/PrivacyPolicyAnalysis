From python:2.7

RUN apt-get update
RUN apt-get upgrade -y

RUN pip install spacy==2.0.12 --no-cache-dir
RUN python -m spacy download en
RUN python -m spacy download en_core_web_lg
RUN pip install networkx
RUN pip install lxml
RUN pip install pandas
RUN pip install enum34

COPY ./code/ /src/

WORKDIR /src
ENTRYPOINT ["/src/main.sh"]
