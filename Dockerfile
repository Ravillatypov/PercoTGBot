FROM python:3.8-alpine

COPY requirements.txt ./

RUN apk add --update --no-cache --virtual .tmp-build-deps build-base python3-dev && \
    pip install --no-cache-dir --no-use-pep517 -r requirements.txt && \
    apk del .tmp-build-deps

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
