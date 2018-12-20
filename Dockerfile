FROM python:3.6-slim

WORKDIR /muni

RUN apt-get update && apt-get install -y wget

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

COPY ./requirements.txt /muni/requirements.txt

RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . /muni

CMD ["dockerize", "-wait", "tcp://database:5432", "python", "manage.py", "run"]
