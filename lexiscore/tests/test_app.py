"""Testing fastws exists service."""
import pytest
from fastapi.testclient import TestClient
from lexiscore.app import app


class ASGITestClient(TestClient):
    """Test client that starts and stops the app on enter and exit."""

    async def __aenter__(self):
        await self.app.router.startup()
        return super().__aenter__()

    async def __aexit__(self, *args, **kwargs):
        await self.app.router.shutdown()
        return await super().__aexit__(*args, **kwargs)


@pytest.fixture(scope="module")
def test_client() -> None:
    with ASGITestClient(app) as client:
        yield client


THRESHOLD = 0.0001
CHECK_KEYS = ["word", "valid", "score"]


def test_health(test_client: TestClient) -> None:
    """Test healthcheck."""
    response = test_client.get("/health")
    assert response.status_code == 200


def test_check(test_client: TestClient) -> None:
    """Test the check endpoint."""
    word = "husar"
    response = test_client.get(f"/check/{word}")
    json = response.json()
    assert isinstance(json, dict) is True
    assert list(json.keys()) == CHECK_KEYS
    assert json["word"] == word
    assert json["valid"] is True
    assert json["score"] > THRESHOLD


def test_check_invalid_word(test_client: TestClient) -> None:
    """Test the check endpoint."""
    word = "ffffft"
    response = test_client.get(f"/check/{word}")
    json = response.json()
    assert isinstance(json, dict) is True
    assert list(json.keys()) == CHECK_KEYS
    assert json["word"] == word
    assert json["valid"] is False
    assert json["score"] < THRESHOLD


def test_language_ranking(test_client: TestClient) -> None:
    """Test the language ranking endpoint."""
    word = "husene"
    response = test_client.get(f"/lang/{word}?languages=da,de,eng")
    json = response.json()
    assert isinstance(json, list) is True
    assert len(json) > 1
    assert json[0][0] == "da"
    assert json[0][1] > THRESHOLD


def test_bulklang_endpoint(test_client: TestClient):
    """Test the bulklang endpoint with no languages provided."""
    # Define the input data
    input_data = {"words": "første,halløj,zwicschen,there", "languages": "da,de,en"}
    response = test_client.get("/bulklang", params=input_data)

    # Ensure the status code is correct
    assert response.status_code == 200

    # Ensure the response content is correct
    response_content = response.json()
    assert "words" in response_content
    assert "results" in response_content
    assert "lang_count" in response_content

    # Ensure the word list is correct
    assert response_content["words"] == input_data["words"]

    # Ensure that results are correct
    results = response_content["results"]
    words_in_result = [result["word"] for result in results]
    assert len(results) == 4
    assert isinstance(results, list) is True
    assert isinstance(results[0], dict) is True
    assert "word" in results[0]
    assert "langs" in results[0]

    # Assert that the words in the result are the same as the input words
    assert words_in_result == input_data["words"].split(",")
    # Assert langs
    langs_of_first = results[0]["langs"]
    assert isinstance(langs_of_first, list) is True
    assert isinstance(langs_of_first[0], list) is True
    assert langs_of_first[0][0] == "da"

    # Assert that lang_count is correct
    lang_count = response_content["lang_count"]
    assert isinstance(lang_count, list) is True
    assert isinstance(lang_count[0], list) is True
    assert lang_count[0][0] == "da"
    assert lang_count[0][1] == 2
