# LexiScore

Return a score for the likelyhood of a word belonging to a certain language based on ngram probabilities

## Run in Docker

```bash
docker compose up
```

The webservice will now be accessible on localhost:9002

## Endpoints

See localhost:9002/docs

## Usage

```python
import requests
from json import loads

URL = "http://localhost:9002"
word = "husar"
params = {"lang": "da"}

response = requests.get(f"{URL}/check/{word}", params=params)
result = loads(response.text)

params = {}
response = requests.get(f"{URL}/lang/{word}", params=params)
result = loads(response.text)

```