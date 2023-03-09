"""FastAPI service for wordres."""
import logging
import os
import pandas as pd
from fastapi import FastAPI
from fastapi_simple_security import api_key_router
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse

from dslsplit import CONFIG
from dslsplit.brute_split import load_probabilities, split_compound
from dslsplit.train_splitter import train_splitter

from dslsplit.splitter import Splitter2

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


title = CONFIG.get("splitter", "title")
description = CONFIG.get("splitter", "description")
# compound_split_probabilities = CONFIG.get("splitter", "prob_file")
word_file_path = CONFIG.get("splitter", "word_file")

app = FastAPI(
    title=title,
    description="description",
)

app.include_router(api_key_router, prefix="/auth", tags=["_auth"])


@app.get("/health", response_class=PlainTextResponse)
def healthcheck() -> str:
    """Healthcheck, for use in automatic ."""
    return "200"


logger.info(f'Train splitter with "{word_file_path}"')
compound_split_probabilities = train_splitter(word_file_path, "careful", lang="da")
lemmas = pd.read_csv(word_file_path, sep=";", usecols=[0], names=["name"])
lemmas = lemmas.name.drop_duplicates().values

splitter = Splitter2(language="da", lemma_list=list(lemmas)).load_from_filepath(
    compound_split_probabilities
)


# @app.get("/split/{word}", response_class=JSONResponse)
# def split(word: str, lang: str = "da", period: str | None = None) -> JSONResponse:
#     """
#     Return word split into tokens and scores and scores for each possible split

#     - **word**: word to split into subtokens
#     - **lang**: language ("da" for Danish or "de" for german)
#     - **period**: for future functionality
#     """
#     splitter.language = lang
#     splits = splitter.easy_split(word)
#     return JSONResponse(content={"word": word, "splits": splits})

brute_probabilities = load_probabilities()


@app.get("/split/{word}", response_class=JSONResponse)
async def split(
    word: str, method: str = "mixed", variant: str = "nudansk", lang: str = "da"
) -> JSONResponse:
    """
    Return word split into tokens and scores and scores for each possible split

    - **word**: word to split into subtokens
    - **lang**: language (Only "da" for Danish is supported)
    - **method**: "mixed" (default), "careful" or "brute"
    - **variant**: "nudansk" (default) or "yngrenydansk"

    """
    if method not in ("mixed", "careful", "brute"):
        raise ValueError(f"Method {method} not supported")
    if variant not in ("nudansk", "yngrenydansk"):
        raise ValueError(f"Variant {variant} not supported")
    if lang not in ("da"):
        raise ValueError(f"Language {lang} not supported")

    splits = {}
    if method in ("careful", "mixed"):
        splitter.language = lang
        splits = splitter.easy_split(word)
        splits = [split for split in splits if split["score"] > 0]
        if splits:
            method = "careful"
    if not splits and method not in ("careful",):
        brute_split = split_compound(word, brute_probabilities[variant])
        splits = brute_split.get("splits", [])
        method = "brute"

    message = {
        "word": word,
        "splits": splits,
        "method": method,
        "description": CONFIG.has_option(method, "description")
        and CONFIG.get(method, "description")
        or "",
    }
    return JSONResponse(content=message)
