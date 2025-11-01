"""
Fuzzy matching utilities for handling typos and variations in state/crop names.
Uses Levenshtein distance for string similarity.
"""
from typing import Optional, List, Tuple
import pandas as pd


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    This measures the minimum number of single-character edits needed to change s1 to s2.
    """
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    # Create a matrix to store distances
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize first row and column
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],  # deletion
                    dp[i][j - 1],  # insertion
                    dp[i - 1][j - 1],  # substitution
                )

    return dp[m][n]


def similarity_score(s1: str, s2: str) -> float:
    """
    Calculate similarity score between 0 and 1 (1 = identical, 0 = completely different).
    """
    s1_lower = s1.lower()
    s2_lower = s2.lower()

    if s1_lower == s2_lower:
        return 1.0

    distance = levenshtein_distance(s1_lower, s2_lower)
    max_len = max(len(s1), len(s2))

    return 1.0 - (distance / max_len) if max_len > 0 else 0.0


def find_best_match(
    query: str, candidates: List[str], threshold: float = 0.7
) -> Optional[Tuple[str, float]]:
    """
    Find the best matching string from a list of candidates.

    Args:
        query: The string to match
        candidates: List of possible matches
        threshold: Minimum similarity score (0-1) to consider a match

    Returns:
        Tuple of (best_match, score) or None if no match above threshold
    """
    if not query or not candidates:
        return None

    best_match = None
    best_score = 0.0

    for candidate in candidates:
        score = similarity_score(query, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold:
        return (best_match, best_score)

    return None


def fuzzy_match_in_dataframe(
    df: pd.DataFrame, column: str, query: str, threshold: float = 0.7
) -> Optional[str]:
    """
    Find the best fuzzy match for a query in a specific DataFrame column.

    Args:
        df: The DataFrame to search
        column: The column name to search in
        query: The value to match
        threshold: Minimum similarity score (0-1) to consider a match

    Returns:
        The best matching value from the column, or None if no match
    """
    if column not in df.columns:
        return None

    unique_values = df[column].dropna().unique().tolist()
    result = find_best_match(query, unique_values, threshold)

    return result[0] if result else None


# Common crop name synonyms and variations
CROP_SYNONYMS = {
    "rice": ["paddy", "rice", "dhan"],
    "paddy": ["paddy", "rice", "dhan"],
    "maize": ["maize", "corn", "makka"],
    "corn": ["maize", "corn", "makka"],
    "millet": ["millet", "pearl millet", "bajra", "bajri"],
    "pearl millet": ["millet", "pearl millet", "bajra", "bajri"],
    "bajra": ["millet", "pearl millet", "bajra", "bajri"],
    "wheat": ["wheat", "gehun", "gehu"],
    "sugarcane": ["sugarcane", "sugar cane", "ganna"],
}


def get_crop_synonyms(crop: str) -> List[str]:
    """
    Get list of known synonyms for a crop name.

    Args:
        crop: The crop name to look up

    Returns:
        List of synonym strings, or [crop] if no synonyms found
    """
    crop_lower = crop.lower().strip()
    return CROP_SYNONYMS.get(crop_lower, [crop])


def find_crop_with_synonyms(
    df: pd.DataFrame, crop_column: str, query_crop: str, threshold: float = 0.7
) -> Optional[str]:
    """
    Find a crop in the DataFrame considering both fuzzy matching and synonyms.

    Args:
        df: The DataFrame to search
        crop_column: The column name containing crop names
        query_crop: The crop name to search for
        threshold: Minimum similarity score for fuzzy matching

    Returns:
        The matched crop name from the DataFrame, or None
    """
    # First try exact match (case-insensitive)
    unique_crops = df[crop_column].dropna().unique()
    for crop in unique_crops:
        if crop.lower() == query_crop.lower():
            return crop

    # Try synonyms
    synonyms = get_crop_synonyms(query_crop)
    for synonym in synonyms:
        for crop in unique_crops:
            if crop.lower() == synonym.lower():
                return crop

    # Finally try fuzzy matching
    return fuzzy_match_in_dataframe(df, crop_column, query_crop, threshold)
