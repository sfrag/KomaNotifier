from saturn_koma_watcher.scoring import score_texts


def test_title_weighs_more_than_description() -> None:
    score_title, terms_title = score_texts("土星こま", "")
    score_desc, terms_desc = score_texts("", "土星こま")

    assert score_title > score_desc
    assert "土星こま" in terms_title
    assert "土星こま" in terms_desc


def test_bonus_for_multiple_matches() -> None:
    score, terms = score_texts("土星こま The Saturn mh044 広井政昭", "江戸独楽 二重構造")
    assert score >= 150
    assert "土星こま" in terms
    assert "The Saturn" in terms
    assert "mh044" in terms
