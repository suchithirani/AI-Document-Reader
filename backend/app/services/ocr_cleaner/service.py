"""
OCR Text Cleaner
================
Pre-processes raw OCR chunk text before it is sent to the LLM.

Responsibilities:
  - Convert word-form numeric amounts to clean numeric strings.
    e.g.  "Five Hundred Forty One And Sixty Six Paise Only" → "541.66"
          "Four Hundred Forty Only"                         → "440.00"
          "Three Thousand Two Hundred And Fifty Cents Only" → "3200.50"

This is language/domain-agnostic: it works for any currency whose
sub-unit (paise, cents, pence, fils, etc.) represents 1/100 of the
main unit and whose amounts are expressed as English number words.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Number-word lookup tables
# ---------------------------------------------------------------------------

_ONES: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}

_TENS: dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

_MULTIPLIERS: dict[str, int] = {
    "hundred": 100,
    "thousand": 1_000,
    "lakh": 100_000,
    "crore": 10_000_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
}

# Words that are legal inside a word-form number expression
_NUMBER_WORDS: set[str] = (
    set(_ONES) | set(_TENS) | set(_MULTIPLIERS)
)

# Sub-unit labels whose presence signals this is a fractional (decimal) part.
# When present the converted value is the DECIMAL component (divide by 100).
_SUB_UNITS: set[str] = {
    "paise", "paisa", "cents", "cent",
    "pence", "penny", "pennies", "fils",
}

# Words that are legal noise/connectors inside an amount phrase
_NOISE: set[str] = {"and", "only", "rupees", "rupee", "dollars", "dollar",
                    "pounds", "pound"}


# ---------------------------------------------------------------------------
# Core converter
# ---------------------------------------------------------------------------

def _words_to_int(tokens: list[str]) -> int | None:
    """
    Convert a flat list of lowercase number-word tokens to an integer.
    Returns None if nothing meaningful was found.
    """
    current: int = 0
    result: int = 0

    for tok in tokens:
        if tok in _ONES:
            current += _ONES[tok]
        elif tok in _TENS:
            current += _TENS[tok]
        elif tok == "hundred":
            current = (current or 1) * 100
        elif tok in _MULTIPLIERS:
            mult = _MULTIPLIERS[tok]
            result += (current or 1) * mult
            current = 0
        # noise words ("and", "only", currency names) are silently skipped

    result += current
    return result if (result or current == 0) else None


# ---------------------------------------------------------------------------
# Pattern & replacement
# ---------------------------------------------------------------------------

# Build a single alternation of all recognised number-word + noise tokens
_ALL_WORDS = sorted(
    _NUMBER_WORDS | _NOISE | _SUB_UNITS,
    key=len, reverse=True,          # longest first so regex is greedy
)
_WORD_ALT = "|".join(re.escape(w) for w in _ALL_WORDS)

# The full pattern matches a sequence of word-number tokens (possibly
# interspersed with noise / sub-unit words) optionally terminated by "only".
# The pattern deliberately stops at a newline so it never merges lines.
_AMOUNT_RE = re.compile(
    r"\b((?:(?:" + _WORD_ALT + r")[^\S\n]+){2,})(?:only\b)?",
    re.IGNORECASE,
)


def _replace_amount(m: re.Match) -> str:  # type: ignore[type-arg]
    """Replacement function called for each regex match."""
    raw = m.group(0).strip()
    tokens = raw.lower().split()

    # Separate tokens into: whole-part tokens, sub-unit label, frac-part tokens
    whole_tokens: list[str] = []
    frac_tokens: list[str] = []
    found_sub_unit = False
    in_frac = False

    for tok in tokens:
        if tok in _SUB_UNITS:
            found_sub_unit = True
            in_frac = True          # everything after this belongs to fraction
            continue
        if tok in {"only"}:
            continue
        if tok == "and" and not in_frac:
            # "And" between whole and fractional parts — switch sides
            in_frac = True
            continue
        if in_frac:
            frac_tokens.append(tok)
        else:
            whole_tokens.append(tok)

    # Filter out noise words that aren't number words
    whole_tokens = [t for t in whole_tokens if t in _NUMBER_WORDS]
    frac_tokens  = [t for t in frac_tokens  if t in _NUMBER_WORDS]

    if not whole_tokens:
        return raw  # nothing useful — leave untouched

    whole_val = _words_to_int(whole_tokens)
    if whole_val is None:
        return raw

    if frac_tokens and found_sub_unit:
        # Fractional part is in sub-units (1/100 of main unit)
        frac_val = _words_to_int(frac_tokens)
        if frac_val is not None:
            numeric = whole_val + frac_val / 100.0
            return f"{numeric:,.2f}"

    return f"{whole_val:,.2f}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clean_ocr_text(text: str) -> str:
    """
    Replace word-form numeric amounts in *text* with their numeric equivalents.

    Examples
    --------
    >>> clean_ocr_text("TotalGST: Five Hundred Forty One And Sixty Six Paise Only")
    'TotalGST: 541.66'

    >>> clean_ocr_text("Four Hundred Forty Only")
    '440.00'

    >>> clean_ocr_text("Grand Total: Nine Thousand And Fifty Cents Only")
    'Grand Total: 9,000.50'
    """
    return _AMOUNT_RE.sub(_replace_amount, text)
