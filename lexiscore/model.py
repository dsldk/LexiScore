import os
import pickle
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from lexiscore import CONFIG, logger, async_timeit

current_dir = Path(__file__).parent.resolve()


@async_timeit
async def load_languages(force_training: bool = False) -> Dict[str, Dict[str, float]]:
    """Load and train all languages from the config file.

    Args:
        force_training: force training, otherwise pickled versions are used if they are present. Defaults to False.

    Returns:
        a dictionary with the languages keys and propability dictionaries as values.
    """
    logger.info(f"Loading languages")
    languages = CONFIG.get("general", "languages").split(",")

    result = {}
    for lang in languages:
        lang = lang.strip()
        result[lang] = await get_probabilties(lang, force_training)

    return result


@async_timeit
async def get_probabilties(lang: str, force_training: bool = False) -> Dict[str, float]:
    """Return probabilities for a given language.

    Args:
        lang: the language to get probabilities for. The language must be present in the config file with a filename supplied.
        force_training: force training, otherwise pickled versions are used if they are present. Defaults to False.

    Returns:
        a dictionary with the character ngrams as keys and the probabilities as values.
    """
    logger.info(f"Getting probabilities for {lang}")
    # Try to unpickle ngram probabilities. If that fails, train the splitter
    # and pickle the ngram probabilities.
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
    """Calculate n-gram probabilities for a corpus.

    Args:
        corpus_file: the filepath to a file with a list of words
        lower: lowercase all words. Defaults to True.
        ngram_length: the length of the ngram to use. Defaults to 4.

    Returns:
        a dictionary with the ngrams as keys and the probabilities as values.
    """
    # Create an empty dictionary to store ngram counts
    ngram_counts = defaultdict(int)

    # Initialize the total count to zero
    total_count = 0
    filepath = current_dir / corpus_file
    with open(filepath, "r") as f:
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
    # Set smoothing parameter
    k = 100

    logger.info(f"Smoothing parameter (Laplace): {k} (total_count: {total_count})")

    # Calculate ngram probabilities with Laplace smoothing
    ngram_probs = {}
    for ngram, count in ngram_counts.items():
        ngram_probs[ngram] = (count + k) / (total_count + k * len(ngram_counts))
    return ngram_probs


@async_timeit
async def calculate_word_probability(
    word: str, ngram_probs: dict, lower: bool = True, ngram_length: int = 4
) -> float:
    """Generate the probability of a word using ngram probabilities.

    Args:
        word: the word to calculate the probability for
        ngram_probs: the ngram probabilities to use
        lower: lowercase the word. Defaults to True.
        ngram_length: the length of the ngram to use. Defaults to 4.

    Returns:
        the probability of the word
    """
    # Add $ before and after the word depending on ngram_length
    word = "$" * (ngram_length - 1) + word + "$" * (ngram_length - 1)
    if lower:
        word = word.lower()

    # Calculate the probability of each ngram and multiply them together
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
    return word_prob


@async_timeit
async def rank_all_languages(
    word: str, probs: dict, langs: List[str] | None = None
) -> List[Tuple[str, float]]:
    """Use probabilities to rank languages for a word.

    Args:
        word: the word to rank
        probs: a dictionary with probabilities for each language
        langs: the languages to consider, if None all languages are considered. Defaults to None.

    Returns:
        a list of tuples with the language and the probability for the word in that language
    """
    result = []
    for lang in probs:
        if langs and lang not in langs:
            continue
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
