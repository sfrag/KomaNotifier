from __future__ import annotations

from collections import OrderedDict

from saturn_koma_watcher.utils import normalize_text

# Pesos explícitos. El título siempre tiene más peso que la descripción.
TERM_WEIGHTS: "OrderedDict[str, int]" = OrderedDict(
    {
        "土星こま": 50,
        "The Saturn": 45,
        "saturn top": 35,
        "mh044": 40,
        "広井政昭": 25,
        "Hiroi": 20,
        "Masaaki": 15,
        "spinning top": 12,
        "球": 10,
        "球体": 10,
        "内球": 10,
        "二重構造": 10,
        "回転": 8,
        "江戸独楽": 8,
    }
)

STRONG_TERMS = {"土星こま", "The Saturn", "saturn top", "mh044"}
AUTHOR_TERMS = {"広井政昭", "Hiroi", "Masaaki"}
STRUCTURE_TERMS = {"球", "球体", "内球", "二重構造", "回転", "江戸独楽"}


def _contains(haystack: str, needle: str) -> bool:
    if any("A" <= ch <= "z" for ch in needle):
        return needle.lower() in haystack.lower()
    return needle in haystack


def score_texts(title: str, description: str) -> tuple[int, list[str]]:
    """Puntúa un anuncio en base a título y descripción."""
    title_n = normalize_text(title)
    desc_n = normalize_text(description)

    total_score = 0
    matched_terms: list[str] = []

    strong_count = 0
    author_count = 0
    structure_count = 0

    for term, weight in TERM_WEIGHTS.items():
        in_title = _contains(title_n, term)
        in_desc = _contains(desc_n, term)

        if in_title:
            total_score += weight
            matched_terms.append(term)
        elif in_desc:
            total_score += int(weight * 0.6)
            matched_terms.append(term)

        if in_title or in_desc:
            if term in STRONG_TERMS:
                strong_count += 1
            if term in AUTHOR_TERMS:
                author_count += 1
            if term in STRUCTURE_TERMS:
                structure_count += 1

    # Bonus por múltiples coincidencias en diferentes grupos.
    if strong_count >= 2:
        total_score += 12
    if author_count >= 2:
        total_score += 8
    if structure_count >= 3:
        total_score += 6
    if len(matched_terms) >= 5:
        total_score += 10

    return total_score, matched_terms
