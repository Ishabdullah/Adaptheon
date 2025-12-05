import math
import re
from collections import Counter

WORD_RE = re.compile(r"\w+")

def tokenize(text):
    return WORD_RE.findall(text.lower())

def text_to_vector(text):
    words = tokenize(text)
    return Counter(words)

def cosine_similarity(vec1, vec2):
    # Pure-Python cosine similarity between two Counters
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)

    sum1 = sum(v * v for v in vec1.values())
    sum2 = sum(v * v for v in vec2.values())
    if not sum1 or not sum2:
        return 0.0

    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    return float(numerator) / denominator
