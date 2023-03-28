import os
import pickle
import tempfile
from collections import defaultdict
from typing import Dict, List, Tuple

from lexiscore import CONFIG, logger, async_timeit


@async_timeit
async def load_languages(force_training: bool = False) -> Dict[str, Dict[str, float]]:
    logger.info(f"Loading languages")
    languages = CONFIG.get("general", "languages").split(",")

    result = {}
    for lang in languages:
        lang = lang.strip()
        result[lang] = await get_probabilties(lang, force_training)

    return result


@async_timeit
async def get_probabilties(lang: str, force_training: bool = False) -> Dict[str, float]:
    logger.info(f"Getting probabilities for {lang}")
    # Try to unpickle trigram probabilities. If that fails, train the splitter
    # and pickle the trigram probabilities.
    pickle_file = os.path.join(tempfile.gettempdir(), f"lexiscore_probs_{lang}.pickle")

    if not force_training:
        try:
            with open(pickle_file, "rb") as f:
                probabilities = pickle.load(f)
            logger.info(f"Probabilities for {lang} loaded from {pickle_file}")
            return probabilities
        except FileNotFoundError:
            logger.info(
                f"Probabilities not found. Training probabilities for {lang} ..."
            )

    logger.info(f'Training probabilities for "{lang}" ...')
    filename = CONFIG.get(lang, "filename")
    filepath = os.path.join(CONFIG.get("general", "data_dir"), filename)
    probs = await calculate_ngram_probs(filepath)
    with open(pickle_file, "wb") as f:
        pickle.dump(probs, f)

    return probs


@async_timeit
async def calculate_ngram_probs(
    corpus_file: str, lower: bool = True, ngram_length: int = 4
) -> Dict[str, float]:
    """Calculate n-gram probabilities for a corpus."""
    # Create an empty dictionary to store trigram counts
    ngram_counts = defaultdict(int)

    # Initialize the total count to zero
    total_count = 0

    with open(corpus_file, "r") as f:
        for line in f:
            if lower:
                line = line.lower()
            word = line.strip()
            # Add $ before and after each line in the corpus depeing on ngram_length
            word = "$" * (ngram_length - 1) + word + "$" * (ngram_length - 1)
            # Update the total count and ngram counts for this word
            total_count += len(word) - (ngram_length - 1)
            for i in range(len(word) - (ngram_length - 1)):
                ngram = word[i : i + ngram_length]
                ngram_counts[ngram] += 1

    # # Calculate ngram probabilities
    # ngram_probs = {}
    # for ngram, count in ngram_counts.items():
    #     ngram_probs[ngram] = count / total_count

    # Set smoothing parameter
    k = 100

    logger.info(f"Smoothing parameter (Laplace): {k} (total_count: {total_count})")

    # Calculate ngram probabilities with Laplace smoothing
    # (jeg ved ikke hvad Laplace er, men det siger chatgpt...)
    ngram_probs = {}
    for ngram, count in ngram_counts.items():
        ngram_probs[ngram] = (count + k) / (total_count + k * len(ngram_counts))
    return ngram_probs


@async_timeit
async def calculate_word_probability(
    word: str, ngram_probs: dict, lower: bool = True, ngram_length: int = 4
) -> float:
    # Add $ before and after the word depending on ngram_length
    word = "$" * (ngram_length - 1) + word + "$" * (ngram_length - 1)
    if lower:
        word = word.lower()

    # Calculate the probability of each trigram and multiply them together
    log_output = []
    word_prob = 1.0
    for i in range(len(word) - (ngram_length - 1)):
        ngram = word[i : i + ngram_length]
        if ngram in ngram_probs:
            ngram_prob = ngram_probs[ngram]
        else:
            # If a ngram is not in the ngram probability dictionary, assume a very low probability
            ngram_prob = 1e-20
        log_output.append(f"{ngram}, {str(ngram_prob)}")
        word_prob *= ngram_prob

    log_output.append(str(word_prob))
    log_txt = "\n".join(log_output)
    logger.debug(f"{log_txt}")

    # Normalize the probability by word length
    word_prob = word_prob ** (1.0 / max(1, len(word) - 2))
    print(word_prob)
    return word_prob


@async_timeit
async def rank_all_languages(
    word: str, probs: dict, langs: List[str] | None = None
) -> List[Tuple[str, float]]:
    result = []
    for lang in probs:
        if langs and lang not in langs:
            continue
        print(lang, word)
        score = await calculate_word_probability(word, probs[lang])
        if "-" in word:
            score_mod = await calculate_word_probability(
                word.replace("-", ""), probs[lang]
            )
            score = score if score > score_mod else score_mod
        result.append((lang, score))
    # Sort the result by score
    result.sort(key=lambda x: x[1], reverse=True)
    return result


if __name__ == "__main__":
    pass
