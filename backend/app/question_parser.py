import re
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ParsedQuestion:
    intent: str
    params: Dict


# Match state names (1-3 words max) - more restrictive but case insensitive
STATE_NAME_PATTERN = r"[A-Za-z]+(?:\s+[A-Za-z]+){0,2}"

STATE_PAIR_REGEX = re.compile(
    rf"in\s+({STATE_NAME_PATTERN}?)\s+(?:and|vs\.?|versus|&)\s+({STATE_NAME_PATTERN}?)\b",
    re.IGNORECASE
)
STATE_BETWEEN_REGEX = re.compile(
    rf"between\s+({STATE_NAME_PATTERN}?)\s+(?:and|vs\.?|versus|&)\s+({STATE_NAME_PATTERN}?)\b",
    re.IGNORECASE
)
# For "compare X and Y" or "compare rainfall in X and Y"
COMPARE_STATES_REGEX = re.compile(
    rf"compare\s+(?:.*?\s+in\s+)?({STATE_NAME_PATTERN}?)\s+(?:and|vs\.?|versus|&)\s+({STATE_NAME_PATTERN}?)\b",
    re.IGNORECASE
)


def _extract_years(text: str) -> Optional[int]:
    # Support multiple phrasings for year ranges
    patterns = [
        r"(?:last|past|previous|recent)\s+(\d+)\s+years?",
        r"over\s+(?:the\s+)?(?:last|past|previous)?\s*(\d+)\s+years?",
        r"during\s+(?:the\s+)?(?:last|past|previous)?\s*(\d+)\s+years?",
        r"for\s+(?:the\s+)?(?:last|past|previous)?\s*(\d+)\s+years?",
        r"in\s+(?:the\s+)?(?:last|past|previous)?\s*(\d+)\s+years?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _extract_top_m(text: str) -> int:
    # Support multiple phrasings for top N
    patterns = [
        r"(?:top|first|best|leading|main)\s+(\d+)",
        r"(\d+)\s+(?:most|top|best|leading|main)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 3


def _clean_token(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return re.sub(r"\s+", " ", value.strip())


def _normalize_state_name(state: Optional[str]) -> Optional[str]:
    """Normalize state name to title case for consistency."""
    if not state:
        return None
    # Handle special cases like "Tamil Nadu"
    words = state.split()
    return " ".join(word.capitalize() for word in words)


def _extract_state_pair(text: str) -> tuple[Optional[str], Optional[str]]:
    # Try direct "in State1 and State2" pattern
    direct = STATE_PAIR_REGEX.search(text)
    if direct:
        return _normalize_state_name(_clean_token(direct.group(1))), _normalize_state_name(_clean_token(direct.group(2)))

    # Try "between State1 and State2" pattern
    between = STATE_BETWEEN_REGEX.search(text)
    if between:
        return _normalize_state_name(_clean_token(between.group(1))), _normalize_state_name(_clean_token(between.group(2)))

    # Try "compare State1 and State2" pattern
    compare = COMPARE_STATES_REGEX.search(text)
    if compare:
        return _normalize_state_name(_clean_token(compare.group(1))), _normalize_state_name(_clean_token(compare.group(2)))

    # Fallback: look for placeholder patterns
    placeholders = re.findall(r"state[_\s]?([A-Za-z]+)", text, re.IGNORECASE)
    if len(placeholders) >= 2:
        return _normalize_state_name(_clean_token(placeholders[0])), _normalize_state_name(_clean_token(placeholders[1]))

    return None, None


def _extract_region(text: str) -> Optional[str]:
    match = re.search(r"in\s+([A-Za-z\s]+?)(?:\s+over|\s+during|\s+across|,|\.|\?|$)", text, re.IGNORECASE)
    if match:
        return _normalize_state_name(_clean_token(match.group(1)))
    match = re.search(r"region[_\s]?([A-Za-z]+)", text, re.IGNORECASE)
    if match:
        return _normalize_state_name(_clean_token(match.group(1)))
    return None


def _extract_crop(text: str) -> Optional[str]:
    match = re.search(r"crop(?:_type)?[_\s]?([A-Za-z]+)", text, re.IGNORECASE)
    if match:
        return _clean_token(match.group(1))
    match = re.search(r"production trend of\s+([A-Za-z\s]+?)\s+in", text, re.IGNORECASE)
    if match:
        return _clean_token(match.group(1))
    match = re.search(r"production of\s+([A-Za-z\s]+?)(?:\s+in|\s+over|,|\.|\?|$)", text, re.IGNORECASE)
    if match:
        return _clean_token(match.group(1))
    return None


def _extract_crop_pair(text: str) -> list[str]:
    crops = re.findall(r"crop[_\s]?type[_\s]?([A-Za-z]+)", text, re.IGNORECASE)
    if crops:
        return [_clean_token(c) for c in crops]
    promote_match = re.search(
        r"promote\s+([A-Za-z\s]+?)\s+over\s+([A-Za-z\s]+?)(?:\s+in|\s+across|\.|$)",
        text,
        re.IGNORECASE,
    )
    if promote_match:
        return [_clean_token(promote_match.group(1)), _clean_token(promote_match.group(2))]
    return []


def parse_question(question: str) -> ParsedQuestion:
    text = question.strip()
    lowered = text.lower()

    if "rainfall" in lowered and ("top" in lowered or "list" in lowered) and "crop" in lowered:
        state_a, state_b = _extract_state_pair(text)
        crop_filter = None
        crop_phrase = re.search(r"crops of ([A-Za-z\s]+?)(?:\(|for|in|,|\.|$)", text, re.IGNORECASE)
        if crop_phrase:
            crop_filter = _clean_token(crop_phrase.group(1))
        else:
            crop_filter = _extract_crop(text)
        params = {
            "state_a": state_a,
            "state_b": state_b,
            "years": _extract_years(lowered),
            "top_m": _extract_top_m(lowered),
            "crop_filter": crop_filter,
        }
        return ParsedQuestion(intent="compare_rainfall_and_crops", params=params)

    # Check for district extremes with various keywords
    has_high = any(word in lowered for word in ["highest", "max", "maximum", "peak", "best", "top"])
    has_low = any(word in lowered for word in ["lowest", "min", "minimum", "worst", "bottom"])

    if "district" in lowered and has_high and has_low:
        state_a, state_b = _extract_state_pair(text)
        inline_states = [
            _normalize_state_name(_clean_token(s))
            for s in re.findall(
                r"\bin\s+([A-Za-z\s]+?)(?=\s+(?:and|with|having|showing|that|had|for|,|\?|\.|$))",
                text,
                re.IGNORECASE,
            )
            if _clean_token(s)
        ]
        inline_states = [
            s
            for s in inline_states
            if s
            and not any(token in STATE_EXCLUDE_TOKENS for token in s.lower().split())
        ]
        if not state_a and inline_states:
            state_a = inline_states[0]
        if (not state_b) and len(inline_states) > 1:
            state_b = inline_states[1]
        if not state_a:
            high_state_match = re.search(
                r"districts?\s+in\s+([A-Za-z\s]+?)\s+(?:with|having|showing|had)",
                text,
                re.IGNORECASE,
            )
            if high_state_match:
                state_a = _normalize_state_name(_clean_token(high_state_match.group(1)))
        if not state_b:
            low_state_match = re.search(
                r"(?:lowest|minimum|min)\s+production\s+of\s+[A-Za-z\s]+?\s+in\s+([A-Za-z\s]+?)(?:\s|,|\.|\?|$)",
                text,
                re.IGNORECASE,
            )
            if low_state_match:
                state_b = _normalize_state_name(_clean_token(low_state_match.group(1)))
        crop = _extract_crop(text)
        if not crop:
            crop_phrase = re.search(
                r"highest production of\s+([A-Za-z\s]+?)\s", text, re.IGNORECASE
            )
            if crop_phrase:
                crop = _clean_token(crop_phrase.group(1))
        year_match = re.search(r"most recent year|(\d{4})", lowered)
        year = None
        if year_match and year_match.group(1):
            year = int(year_match.group(1))
        params = {
            "state_a": state_a,
            "state_b": state_b,
            "crop": crop,
            "year": year,
        }
        return ParsedQuestion(intent="district_extremes", params=params)

    # Production trend - catch "trend" or "show" with crop and region
    if "trend" in lowered or "show" in lowered:
        region = _extract_region(text)
        crop = _extract_crop(text)
        # If we have both region and crop, it's likely a trend query
        if region and crop:
            params = {
                "region": region,
                "crop": crop.title() if crop else None,
                "years": _extract_years(lowered),
            }
            return ParsedQuestion(intent="production_trend_with_climate", params=params)

    # Policy arguments - catch "policy", "scheme", or "promote"
    if "policy" in lowered or "scheme" in lowered or "promote" in lowered:
        crops = [c for c in _extract_crop_pair(text) if c]
        region = _extract_region(text)
        params = {
            "region": region,
            "crop_a": crops[0] if crops else None,
            "crop_b": crops[1] if len(crops) > 1 else None,
            "years": _extract_years(lowered),
        }
        return ParsedQuestion(intent="policy_arguments", params=params)

    # Fallback heuristics for looser phrasing
    state_a, state_b = _extract_state_pair(text)
    crop = _extract_crop(text)

    if "rainfall" in lowered and state_a and state_b:
        params = {
            "state_a": state_a,
            "state_b": state_b,
            "years": _extract_years(lowered),
            "top_m": _extract_top_m(lowered),
            "crop_filter": crop,
        }
        return ParsedQuestion(intent="compare_rainfall_and_crops", params=params)

    if "district" in lowered and state_a and state_b and crop:
        params = {
            "state_a": state_a,
            "state_b": state_b,
            "crop": crop,
            "year": None,
        }
        return ParsedQuestion(intent="district_extremes", params=params)

    if "trend" in lowered and (crop or "production" in lowered):
        region = _extract_region(text)
        params = {
            "region": region,
            "crop": crop.title() if crop else None,
            "years": _extract_years(lowered),
        }
        return ParsedQuestion(intent="production_trend_with_climate", params=params)

    if ("promote" in lowered or "compare" in lowered) and crop:
        crops = _extract_crop_pair(text)
        params = {
            "region": _extract_region(text),
            "crop_a": crops[0] if crops else crop,
            "crop_b": crops[1] if len(crops) > 1 else None,
            "years": _extract_years(lowered),
        }
        return ParsedQuestion(intent="policy_arguments", params=params)

    return ParsedQuestion(intent="unknown", params={"raw": question})
STATE_EXCLUDE_TOKENS = {
    "most",
    "recent",
    "year",
    "available",
    "lowest",
    "highest",
    "district",
    "compare",
    "that",
    "with",
    "the",
}
