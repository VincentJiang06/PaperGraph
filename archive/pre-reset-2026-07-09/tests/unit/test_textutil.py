"""Unit tests for the shared text algorithms (docs/09 §0)."""

from __future__ import annotations

import pytest

from paperproof import textutil as tu

pytestmark = pytest.mark.unit


def test_normalize_collapses_and_strips():
    assert tu.normalize("  a\t b\n\n c  ") == "a b c"
    assert tu.normalize("Å") == "Å"  # NFC keeps precomposed
    # NFD combining sequence -> NFC precomposed (same normalized form)
    assert tu.normalize("Å") == tu.normalize("Å")


def test_casefold():
    assert tu.casefold("HeLLo   World") == "hello world"
    assert tu.casefold("STRASSE") == "strasse"


def test_is_cjk_ranges():
    assert tu.is_cjk("中")  # CJK unified
    assert tu.is_cjk("㐀")  # Extension A
    assert tu.is_cjk("あ")  # Hiragana
    assert tu.is_cjk("ア")  # Katakana
    assert tu.is_cjk("한")  # Hangul syllable
    assert not tu.is_cjk("a")
    assert not tu.is_cjk("1")
    assert not tu.is_cjk("é")


def test_tokens_alnum_and_cjk():
    assert tu.tokens("Hello, world!") == ["hello", "world"]
    assert tu.tokens("de-risking LDI") == ["de", "risking", "ldi"]
    assert tu.tokens("你好 world") == ["你", "好", "world"]
    assert tu.tokens("!!!  ") == []


def test_word_count_cjk_is_one_each():
    assert tu.word_count("Hello world") == 2
    assert tu.word_count("你好 world") == 3  # 你, 好, world
    assert tu.word_count("de-risking") == 2


def test_sentence_split_ascii_needs_trailing_ws():
    assert tu.sentence_split("One. Two. Three.") == ["One.", "Two.", "Three."]
    # ascii terminator not followed by whitespace does not split
    assert tu.sentence_split("3.14 is pi") == ["3.14 is pi"]
    assert tu.sentence_count("3.14 is pi") == 1
    # trailing fragment without terminator counts
    assert tu.sentence_count("no terminator here") == 1


def test_sentence_split_cjk_always():
    assert tu.sentence_split("第一。第二！第三？") == ["第一。", "第二！", "第三？"]
    # CJK terminator with no following space still splits
    assert tu.sentence_count("a。b") == 2
    assert tu.sentence_count("Hello。world") == 2


def test_contains_case_insensitive():
    assert tu.contains("Hello World", "hello")
    assert tu.contains("Hello World", "WORLD")
    assert not tu.contains("abc", "xyz")


def test_quote_match_preserves_case_normalizes_ws():
    assert tu.quote_match("The  quick brown fox", "quick brown")
    assert tu.quote_match("a\n b", "a b")
    assert not tu.quote_match("The Quick", "quick")  # case preserved


def test_scope_compatible_period():
    assert tu.scope_compatible({"period": "2020-2023"}, {"period": "2022"})
    assert not tu.scope_compatible({"period": "2019"}, {"period": "2020-2023"})
    # unparseable period -> substring test either direction
    assert tu.scope_compatible({"period": "Q3 2022"}, {"period": "2022"})


def test_scope_compatible_region_actors():
    assert tu.scope_compatible({"region": "UK"}, {"region": "uk"})
    assert not tu.scope_compatible({"region": "UK"}, {"region": "US"})
    assert tu.scope_compatible({"actors": ["A", "B"]}, {"actors": ["b", "c"]})
    assert not tu.scope_compatible({"actors": ["A"]}, {"actors": ["X"]})


def test_scope_compatible_missing_keys_never_conflict():
    assert tu.scope_compatible({"period": "2022"}, {"region": "UK"})
    assert tu.scope_compatible({}, {"region": "UK"})


def test_stopwords_frozen_verbatim():
    # The docs/09 §0 verbatim list; the doc's parenthetical "(72 words)" is a
    # mislabel of the actual 82-word list (recorded in OPEN DOC ISSUES).
    assert len(tu.STOPWORDS) == 82
    for w in ("a", "an", "the", "against", "between", "its", "as", "being"):
        assert w in tu.STOPWORDS
    for w in ("liquidity", "pension", "risk"):
        assert w not in tu.STOPWORDS


def test_scope_compatible_endash_period_range():
    """F9 (docs/09 §0, D10): a contract period written with an en dash
    ("2020–2025") is compatible with a node period written with an ASCII hyphen
    ("2020-2025") — the live run rejected 7/8 nodes on this normalization gap."""
    assert tu.normalize_dashes("2020–2025") == "2020-2025"
    assert tu.scope_compatible({"period": "2020–2025"}, {"period": "2020-2025"})
    # em dash, minus sign and fullwidth tilde variants normalize too.
    assert tu.scope_compatible({"period": "2020—2025"}, {"period": "2022"})
    assert tu.scope_compatible({"period": "2020−2025"}, {"period": "2024-2030"})
    assert not tu.scope_compatible({"period": "2010–2015"}, {"period": "2020-2025"})
