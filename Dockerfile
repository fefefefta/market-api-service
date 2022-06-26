FROM python:3.8.10-alpine
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install --upgrade pip
WORKDIR /app
COPY ./market /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY ./entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]
