# LexiScore

Return a score for the likelyhood of a word belonging to a certain language based on ngram probabilities.

## API KEYS

Lexiscore uses dsldk/fastapi_simple_security. Three files are needed. Use

```bash
git secret reveal
```

to unpack the .secret versions of the files from the repository. Or create them:

```bash
touch apikeys.prod.txt
touch apikeys.dev.txt
touch secrets.env
```

List the master keyword for Fastapi_simple_security in the `secrets.env` file:

```env
FASTAPI_SIMPLE_SECURITY_SECRET=some_secret_password
```

Use this password to create api-keys from the web interface:

```url
http://localhost:9002/docs
```

List any known api-keys in the apikeys..txt files with format:

```csv
NAME_OF_KEY;API_KEY;EXPIRATION_DATE
```

e.g.:

```csv:
test;2d3922ea-c5cc-4d08-8be5-4c71c23c29f1;2023-12-01
```

## Run in Docker

```bash
docker compose --env-file=dev.env up --build
OR
docker compose --env-file=prod.env up --build
```

The webservice will now be accessible on localhost:9002 or localhost:8002. Ports can be changed in the prod.env and dev.env files. Add "-d" for detached mode.

## Run from terminal (without Docker)

Setup virual environment:

```bash
ACTIVATE ENVIRONMENT
pip install -r requirements.txt
pip install .
```

Setup environment variables:

```bash
export FASTAPI_SIMPLE_SECURITY_SECRET=some_secret_password
export FASTAPI_SIMPLE_SECURITY_API_KEY_FILE=/path/to/apikeys.txt
export LOG_LEVEL=INFO
```

Run:

```bash
cd lexiscore
uvicorn app:app --PORT 8000
```

The webservice should now be accessible on port 8000 with some_secret_password as the master password that can be used to create api-keys to access the actual endpoints from localhost:8000/docs.

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

## Adding a language the local workspace

Added a list of words to lexiscore/data/.

Add a config.ini to extend the default.ini:

```bash
touch lexiscore/config.ini
```

with basic information about the language

```txt
[general]
languages = da,de,en,some_language

[some_language]
filename = some_filename
```
