"""FastAPI service for wordres."""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi_simple_security import api_key_router, api_key_security
from os import environ

from lexiscore import CONFIG, logger
from lexiscore.model import (
    load_languages,
    calculate_word_probability,
    rank_all_languages,
)

enable_security = environ.get("ENABLE_SECURITY", "False").strip()

if enable_security is None:
    raise ValueError("ENABLE_SECURITY not set")

enable_security = enable_security.lower() in ("true", "1") and True or False
security_str = (
    "\033[1;32mENABLED\033[0m" if enable_security else "\033[1;31mDISABLED\033[0m"
)
logger.info(f"Security: {security_str}")


title = CONFIG.get("general", "title")

app = FastAPI(
    title=title,
    description="description",
)

origins = CONFIG.get("webservice", "origin")
logger.info(f"Allowed origins: {origins}")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True)
logger.info(f"Adding API key security")
app.include_router(api_key_router, prefix="/auth", tags=["_auth"])


@app.get("/health", response_class=PlainTextResponse)
def healthcheck() -> str:
    """Healthcheck, for use in automatic verification."""
    return "200"


@app.on_event("startup")
async def startup_event() -> None:
    """Load probabilities on startup."""
    global probabilities
    probabilities = await load_languages(force_training=False)


@app.get(
    "/check/{word}",
    response_class=JSONResponse,
    dependencies=[Depends(api_key_security)],
)
async def check(word: str, lang: str = "da", threshold: float = 0.0001) -> JSONResponse:
    """Check whether word might be a valid word in the given language, based on character pentagrams.

    Args:
        word: the word to check.
        lang: the language to check the word against. Defaults to "da".
        threshold: a threshold value - if the probability of the word is equal to or above, the word is deemed a valid
        word in that language. Defaults to 0.0001.

    Returns:
        {"word": str, "valid": bool, "score": float}
    """
    if lang not in probabilities:
        return JSONResponse(content={"error": "language not found"}, status_code=404)
    score = await calculate_word_probability(word, probabilities[lang])
    message = {"word": word, "valid": score >= threshold, "score": score}
    return JSONResponse(content=message)


@app.get(
    "/lang/{word}",
    response_class=JSONResponse,
    dependencies=[Depends(api_key_security)],
)
async def rank_languages(
    word: str, threshold: float = 0.000001, languages: str | None = None
) -> JSONResponse:
    """Rank the languages, only return languages with score >= threshold.

    Args:
        word: word to check.
        threshold: minimum score to return a language. Defaults to 0.000001. Note that this is a lower threshold
        than the check endpoint, and will return more languages.
        languages: comma-separated list of languages to rank. If not set, all languages are ranked.

    Returns:
        List of (language, score) tuples.
    """
    if languages is not None:
        langs = languages.split(",")
    else:
        langs = None
    result = await rank_all_languages(word, probabilities, langs=langs)
    result = [(lang, score) for lang, score in result if score >= threshold]
    return JSONResponse(content=result)


@app.get(
    "/bulklang",
    response_class=JSONResponse,
    dependencies=[Depends(api_key_security)],
)
async def bulk_rank_languages(
    words: str, threshold: float = 0.000001, languages: str | None = None
) -> JSONResponse:
    """Rank the languages for each word in words, only return languages with score > threshold, and count the number
    of times each language is the first result.

    Args:
        words: comma-separated list of words to check.
        threshold: minimum score to return a language.
        languages: comma-separated list of languages to rank. If not supplied, all languages are ranked.
    Returns:
        {
            "words": str,
            "results": a list of lists of (language, score) tuples
            "lang_count": List[(language, count)]"
        }
    """
    word_list = words.split(",")
    if languages is not None:
        langs = languages.split(",")
    else:
        langs = None
    result = []
    for word in word_list:
        word = word.strip()
        word_result = await rank_all_languages(word, probabilities, langs=langs)
        word_result = [
            (lang, score) for lang, score in word_result if score >= threshold
        ]
        result.append({"word": word, "langs": word_result})
    # Counts the number of times each langauge is the first result
    lang_count = {}
    for word_info in result:
        word_result = word_info["langs"]
        if len(word_result) > 0:
            lang = word_result[0][0]
            lang_count[lang] = lang_count.get(lang, 0) + 1
    # Sorts the languages by the number of times they are the first result
    lang_count = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)

    output = {
        "words": words,
        "results": result,
        "lang_count": lang_count,
    }
    return JSONResponse(content=output)


# Disable API-KEY security if ENABLE_SECURITY is not set or is false
if not enable_security:
    app.dependency_overrides[api_key_security] = lambda: None
