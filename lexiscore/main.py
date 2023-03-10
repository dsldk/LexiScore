import os
import pickle
import tempfile
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

    filename = CONFIG.get(lang, "filename")
    filepath = os.path.join(CONFIG.get("general", "data_dir"), filename)
    probs = calculate_trigram_probs(filepath)
    with open(pickle_file, "wb") as f:
        pickle.dump(probs, f)

    return probs


def calculate_trigram_probs(corpus_file, lower=True):
    # Create an empty dictionary to store trigram counts
    trigram_counts = {}

    # Initialize the total count to zero
    total_count = 0

    # Add $$ before and after each word in the corpus
    with open(corpus_file, "r") as f:
        for line in f:
            if lower:
                line = line.lower()
            word = line.strip()
            word = "$$" + word + "$$"

            # Update the total count and trigram counts for this word
            total_count += len(word) - 2
            for i in range(len(word) - 2):
                trigram = word[i : i + 3]
                if trigram in trigram_counts:
                    trigram_counts[trigram] += 1
                else:
                    trigram_counts[trigram] = 1

    # Calculate trigram probabilities
    trigram_probs = {}
    for trigram, count in trigram_counts.items():
        trigram_probs[trigram] = count / total_count

    return trigram_probs


@timeit
async def calculate_word_probability(word, trigram_probs, lower=True):
    # Add $$ before and after the word
    word = "$$" + word + "$$"
    if lower:
        word = word.lower()

    # Calculate the probability of each trigram and multiply them together
    word_prob = 1.0
    for i in range(len(word) - 2):
        trigram = word[i : i + 3]
        if trigram in trigram_probs:
            word_prob *= trigram_probs[trigram]
        else:
            # If a trigram is not in the trigram probability dictionary, assume a very low probability
            word_prob *= 1e-20

    # Normalize the probability by word length
    word_prob = word_prob ** (1.0 / max(1, len(word) - 2))

    return word_prob


@timeit
async def rank_all_languages(word: str, probs: dict) -> list:
    result = []
    for lang in probs:
        score = await calculate_word_probability(word, probs[lang])
        result.append((lang, score))
    # Sort the result by score
    result.sort(key=lambda x: x[1], reverse=True)
    return result


#    lang1_score = calculate_word_probability(word, lang1)
#    lang2_score = calculate_word_probability(word, lang2)
#    print(f"{word}: {lang1_score} vs {lang2_score}")

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
