"""FastAPI service for wordres."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse

from lexiscore import CONFIG, logger
from lexiscore.main import (
    load_languages,
    calculate_word_probability,
    rank_all_languages,
)

title = CONFIG.get("general", "title")

app = FastAPI(
    title=title,
    description="description",
)


@app.get("/health", response_class=PlainTextResponse)
def healthcheck() -> str:
    """Healthcheck, for use in automatic ."""
    return "200"


@app.on_event("startup")
async def startup_event() -> None:
    global probabilities
    probabilities = await load_languages(force_training=False)


@app.get("/check/{word}", response_class=JSONResponse)
async def check(word: str, lang: str = "da", threshold: float = 0.0001) -> JSONResponse:
    """Check wheter word might be a valid word in the given language."""
    if lang not in probabilities:
        return JSONResponse(content={"error": "language not found"}, status_code=404)
    score = await calculate_word_probability(word, probabilities[lang])
    message = {"word": word, "valid": score >= threshold, "score": score}
    return JSONResponse(content=message)


@app.get("/lang/{word}", response_class=JSONResponse)
async def rank_languages(word: str, threshold: float = 0.0001) -> JSONResponse:
    """Rank the languages, only return languages with score > threshold."""
    result = await rank_all_languages(word, probabilities)
    result = [(lang, score) for lang, score in result if score >= threshold]
    return JSONResponse(content=result)
