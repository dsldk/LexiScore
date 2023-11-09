# LexiScore

Return a score for the likelyhood of a word belonging to a certain language based on ngram probabilities.

## Download

```console
git clone https://github.com/dsldk/lexiscore.git
```

## Security with API keys

Security with API keys can be enabled by setting the environment variable `ENABLE_SECURITY=true`.

Security uses a DSL fork of fastapi_simple_security: [https://github.com/dsldk/fastapi_simple_security]

Security is not activated by default.The following steps is only relevant if security is enabled.

### Master password

Set master keyword for the Swagger UI with the environment variable `FASTAPI_SIMPLE_SECURITY_SECRET`, e.g.:

`FASTAPI_SIMPLE_SECURITY_SECRET=some_secret_password``

### Adding API keys

When enabled, API keys can be added using the Swagger UI for the webservice (reached on /docs url, see below), or be adding a csv file with the following format:

`
NAME_OF_KEY;API_KEY;EXPIRATION_DATE
`

e.g.:

`test;2d3922ea-c5cc-4d08-8be5-4c71c23c29f1;2023-12-01`

The csv file should be set with the environmental variable `FASTAPI_SIMPLE_SECURITY_API_KEY_FILE`, e.g.:

`FASTAPI_SIMPLE_SECURITY_API_KEY_FILE=/path/to/apikeys.txt`

## Run with Docker

To run the webservice with Docker, a Docker client needs to be installed.See [Docker documentation](https://www.docker.com) for details.

### In development mode

```console
docker compose --env-file dev.env up --build
```

Add "-d" switch to run as daemon.

### In production mode

In production mode security is activated and log level is set to warning.

```console
docker compose --env-file prod.env up --build
```

Add "-d" switch to run as daemon.

### Custom environment file

We provide a default development and production environment file.
This is an example of the production file:

```bash
API_KEYS_FILE=./apikeys.prod.txt
LOG_LEVEL=WARNING
PORT=8001
ENABLE_SECURITY=true
```

To create custom development or production modes, simply either change the respective environment files or create a new custom file.

To run Docker with the custom setup, remember to change the parameter `--env-file``

## Run from terminal

Setup virtual environment:

```console
ACTIVATE ENVIRONMENT
pip install -r requirements.txt
pip install .
```

Run with uvicorn:

```bash
cd lexiscore
uvicorn app:app --PORT 8000
```

### Optional setup

Set optional setup environment variables before running to activate API key security:

```bash
ENABLE_SECURITY=true
FASTAPI_SIMPLE_SECURITY_SECRET=some_secret_password
FASTAPI_SIMPLE_SECURITY_API_KEY_FILE=/path/to/apikeys.txt
LOG_LEVEL=INFO
```

The webservice should now be accessible on port 8000 with some_secret_password as the master password that can be used to create api-keys to access the actual endpoints from localhost:8000/docs.

## Setup

### Adding language in local workspace

To add a new language to the local workspace, you need to a file with a list of words from the language.This could either be a lemma list or a full form list.The list should be added to the lexiscore/data directory.

The configuration also needs to be updated.This can be done by adding a config.ini to extend the default.ini:

```bash
touch lexiscore/config.ini
```

The config should include basic information about the language

```txt
[general]
languages = da,de,en,some_language

[some_language]
filename = some_filename
```

## Endpoints

See:

* localhost:9002/docs (development)
* localhost:8002/docs (production)

## Accessing the webservice

```python
import requests
from json import loads

URL = "http://localhost:9002"
word = "husar"
api_key = "2d3922ea-c5cc-4d08-8be5-4c71c23c29f1"
params = {"lang": "da", "api-key": api_key}

response = requests.get(f"{URL}/check/{word}", params=params)
result = loads(response.text)
# {"word":"husar","valid":true,"score":0.00024243456583721002}

params = {"api-key": api_key}
response = requests.get(f"{URL}/lang/{word}", params=params)
result = loads(response.text)
# [["da",0.00024243456583721002],["de",0.00021127065052605355],["da_lemma",0.0001922643763442915],["en",4.605676657984788e-06]]
```
