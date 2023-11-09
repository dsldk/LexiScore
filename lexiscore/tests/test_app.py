"""Testing fastws exists service."""
import pytest
import requests
from fastapi.testclient import TestClient
from lexiscore.app import app


# TODO: Change tests to TestClient


@pytest.fixture(scope="session")
async def test_app():
    # Load the test client
    async with TestClient(app) as client:
        # Call the startup event
        await app.startup()
        # Return the test client
        yield client


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
    assert isinstance(json, dict) is True
    assert list(json.keys()) == CHECK_KEYS
    assert json["word"] == word
    assert json["valid"] is True
    assert json["score"] > THRESHOLD


def test_check_invalid_word() -> None:
    """Test the check endpoint."""
    word = "ffffft"
    url = f"{HOST}/check/{word}"
    response = requests.get(url)
    json = response.json()
    assert isinstance(json, dict) is True
    assert list(json.keys()) == CHECK_KEYS
    assert json["word"] == word
    assert json["valid"] is False
    assert json["score"] < THRESHOLD


def test_language_ranking() -> None:
    """Test the language ranking endpoint."""
    word = "husene"
    url = f"{HOST}/lang/{word}?languages=da,de,eng"
    response = requests.get(url)
    json = response.json()
    assert isinstance(json, list) is True
    assert len(json) > 1
    assert json[0][0] == "da"
    assert json[0][1] > THRESHOLD


# TODO: Fix this test
async def test_bulklang_endpoint_with_no_languages_provided():
    """
    GIVEN a FastAPI app
    WHEN the '/bulklang' endpoint is hit with a list of words and no languages provided
    THEN ensure the endpoint returns a JSON response with correct results and status code
    """
    # Define the input data
    input_data = {"words": "apple,banana,orange,pear"}

    # Hit the endpoint
    response = await test_app.get("/bulklang", params=input_data)

    # Ensure the status code is correct
    assert response.status_code == 200

    # Ensure the response content is correct
    response_content = response.json()
    assert "words" in response_content
    assert "results" in response_content
    assert "lang_count" in response_content

    # Ensure the word list is correct
    assert response_content["words"] == input_data["words"]

    # Ensure the results are correct
    expected_results = [
        [("English", 0.9), ("French", 0.1)],
        [("Spanish", 0.8), ("Portuguese", 0.2)],
        [("English", 0.7), ("Dutch", 0.3)],
        [("English", 1.0)],
    ]
    assert response_content["results"] == expected_results

    # Ensure the language count is correct
    expected_lang_count = [("English", 3), ("Spanish", 1)]
    assert response_content["lang_count"] == expected_lang_count
