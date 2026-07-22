import re


def from_snake_to_camel_case(s: str) -> str:
    """Convert a string from snake_case to camelCase.

    Args:
        s (str): The input string in snake_case.

    Returns:
        str: The string converted to camelCase.
    """
    parts = s.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def from_camel_to_snake_case(s: str) -> str:
    """Convert a string from camelCase to snake_case.

    Args:
        s (str): The input string in camelCase.

    Returns:
        str: The string converted to snake_case.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def to_clean_string(s: str) -> str:
    """Convert a string to snake_case.

    Args:
        s (str): The input string.

    Returns:
        str: The string converted to snake_case.
    """
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    words = re.findall(r"[a-zA-Z]+", s)
    return "_".join(words).lower()


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings.

    Levenshtein distance is a measure of the difference between two strings,
    defined as the minimum number of single-character edits (ins, del, or sub)
    required to change one string into the other. If distance is 0, strings are equal.
    Levelenshtein distance is symmetric.

    Args:
        s1 (str): The first string.
        s2 (str): The second string.

    Returns:
        int: The Levenshtein distance between the two strings.
    """
    m, n = len(s1), len(s2)
    dp = [[0 for _ in range(n + 1)] for _ in range(m + 1)]

    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
    return dp[m][n]


def jaccard_similarity(s1: str, s2: str) -> float:
    """Calculate the Jaccard similarity between two strings.

    Measure of similarity between two sets, defined as the size of the intersection
    divided by the size of the union.

    Args:
        s1 (str): The first string.
        s2 (str): The second string.

    Returns:
        float: The Jaccard similarity between the two strings, ranging from 0 to 1.
    """
    # Convert strings to lowercase and split into sets of words
    set1 = set(s1.lower().split())
    set2 = set(s2.lower().split())

    # Calculate intersection and union
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    # Handle the case of two empty strings
    if union == 0:
        return 1.0

    return intersection / union


def jaro_similarity(s1: str, s2: str) -> float:
    """Calculate the Jaro similarity between two strings.

    Jaro similarity is a string similarity metric designed for short strings,
    based on matching characters and transpositions.

    Args:
        s1 (str): The first string.
        s2 (str): The second string.

    Returns:
        float: The Jaro similarity between the two strings, ranging from 0 to 1
    """
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_dist = (max(len1, len2) // 2) - 1

    match = 0
    hash_s1 = [0] * len1
    hash_s2 = [0] * len2

    # Finding matches
    for i in range(len1):
        for j in range(max(0, i - max_dist), min(len2, i + max_dist + 1)):
            if s1[i] == s2[j] and hash_s2[j] == 0:
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break

    if match == 0:
        return 0.0

    # Finding transpositions
    t = 0
    point = 0
    for i in range(len1):
        if hash_s1[i]:
            while hash_s2[point] == 0:
                point += 1
            if s1[i] != s2[point]:
                t += 1
            point += 1
    t //= 2

    # Jaro Score Formula
    return (match / len1 + match / len2 + (match - t) / match) / 3.0
