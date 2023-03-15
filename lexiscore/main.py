import os
import pickle
import tempfile
from collections import defaultdict
from lexiscore import CONFIG, logger, timeit


@timeit
async def load_languages(force_training: bool = False) -> dict:
    logger.info(f"Loading languages")
    languages = CONFIG.get("general", "languages").split(",")

    result = {}
    for lang in languages:
        lang = lang.strip()
        result[lang] = get_probabilties(lang, force_training)

    return result


@timeit
def get_probabilties(lang: str, force_training: bool = False) -> dict:
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
    probs = calculate_ngram_probs(filepath)
    with open(pickle_file, "wb") as f:
        pickle.dump(probs, f)

    return probs


def calculate_ngram_probs(
    corpus_file: str, lower: bool = True, ngram_length: int = 4
) -> dict:
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


@timeit
async def calculate_word_probability(
    word, ngram_probs, lower=True, ngram_length: int = 4
):
    # Add $ before and after the word depending on ngram_length
    word = "$" * (ngram_length - 1) + word + "$" * (ngram_length - 1)
    if lower:
        word = word.lower()

    # Calculate the probability of each trigram and multiply them together
    word_prob = 1.0
    for i in range(len(word) - (ngram_length - 1)):
        ngram = word[i : i + ngram_length]
        if ngram in ngram_probs:
            ngram_prob = ngram_probs[ngram]
        else:
            # If a ngram is not in the ngram probability dictionary, assume a very low probability
            ngram_prob = 1e-20
        print(ngram, ngram_prob)
        word_prob *= ngram_prob

    print(word_prob)
    # Normalize the probability by word length
    word_prob = word_prob ** (1.0 / max(1, len(word) - 2))
    print(word_prob)
    return word_prob


@timeit
async def rank_all_languages(word: str, probs: dict) -> list:
    result = []
    for lang in probs:
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
    print("hallogit")
    probs = load_languages(force_training=True)
    words = [
        "anders",
        "husar",
        "ffffb",
        "sksksksk",
        "ss",
        "Gott",
        "schwarz",
        "Schwester",
        "substitutionselasticitet",
        "wwwgooglecom",
        "jubiidk",
    ]

    result = []
    for word in words:
        score = calculate_word_probability(word, probs["da"])
        result.append((word, score))

    result.sort(key=lambda x: x[1], reverse=True)

    for word, score in result:
        print(f"{word}: {score}")

    for word in words:
        comp = rank_all_languages(word, probs)
        print(word, comp)
