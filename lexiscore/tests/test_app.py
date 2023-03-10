"""Testing fastws exists service."""
from typing import assert_type
import pytest
import requests

HOST = "http://127.0.0.1:8000"
THRESHOLD = 0.0001
CHECK_KEYS = ["word", "valid", "score"]


def test_health() -> None:
    """Test healthcheck."""
    url = f"{HOST}/health"
    response = requests.get(url)
    assert response.status_code == 200


def test_check() -> None:
    """Test the check endpoint."""
    word = "husar"
    url = f"{HOST}/check/{word}"
    response = requests.get(url)
    json = response.json()
    assert isinstance(json, dict) == True
    assert list(json.keys()) == CHECK_KEYS
    assert json["word"] == word
    assert json["valid"] == True
    assert json["score"] > THRESHOLD


def test_check_invalid_word() -> None:
    """Test the check endpoint."""
    word = "ffffft"
    url = f"{HOST}/check/{word}"
    response = requests.get(url)
    json = response.json()
    assert isinstance(json, dict) == True
    assert list(json.keys()) == CHECK_KEYS
    assert json["word"] == word
    assert json["valid"] == False
    assert json["score"] < THRESHOLD


def test_language_ranking() -> None:
    """Test the language ranking endpoint."""
    word = "husene"
    url = f"{HOST}/lang/{word}"
    response = requests.get(url)
    json = response.json()
    assert isinstance(json, list) == True
    assert len(json) > 1
    assert json[0][0] == "da"
    assert json[0][1] > THRESHOLD
