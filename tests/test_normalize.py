from __future__ import annotations

import pytest

from app.normalize import (
    _first_non_empty,
    _join_creative_bodies,
    _parse_start_date,
    normalize_ad_row,
    utc_now_iso,
)

NOW = "2026-04-18T12:00:00+00:00"


# ── _join_creative_bodies ────────────────────────────────


class TestJoinCreativeBodies:
    def test_none(self):
        assert _join_creative_bodies(None) is None

    def test_empty_list(self):
        assert _join_creative_bodies([]) is None

    def test_single_item(self):
        assert _join_creative_bodies(["Hola mundo"]) == "Hola mundo"

    def test_multiple_items(self):
        assert _join_creative_bodies(["Línea 1", "Línea 2"]) == "Línea 1\nLínea 2"

    def test_blank_strings_filtered(self):
        assert _join_creative_bodies(["", "  ", "Texto"]) == "Texto"

    def test_all_blank(self):
        assert _join_creative_bodies(["", "  "]) is None

    def test_non_list_string(self):
        assert _join_creative_bodies("texto directo") == "texto directo"

    def test_non_list_empty_string(self):
        assert _join_creative_bodies("") is None


# ── _parse_start_date ────────────────────────────────────


class TestParseStartDate:
    def test_iso_date(self):
        assert _parse_start_date("2024-03-15") == "2024-03-15"

    def test_iso_datetime(self):
        assert _parse_start_date("2024-03-15T10:30:00+0000") == "2024-03-15"

    def test_none(self):
        assert _parse_start_date(None) is None

    def test_empty_string(self):
        assert _parse_start_date("") is None

    def test_whitespace(self):
        assert _parse_start_date("   ") is None

    def test_malformed(self):
        assert _parse_start_date("not-a-date") is None

    def test_partial_date(self):
        assert _parse_start_date("2024-13-01") is None  # month 13 invalid


# ── _first_non_empty ─────────────────────────────────────


class TestFirstNonEmpty:
    def test_none_input(self):
        assert _first_non_empty(None) is None

    def test_non_list(self):
        assert _first_non_empty("string") is None

    def test_empty_list(self):
        assert _first_non_empty([]) is None

    def test_returns_first(self):
        assert _first_non_empty(["a", "b"]) == "a"

    def test_skips_blanks(self):
        assert _first_non_empty(["", "  ", "caption"]) == "caption"

    def test_all_blank(self):
        assert _first_non_empty(["", "  "]) is None


# ── normalize_ad_row ─────────────────────────────────────


class TestNormalizeAdRow:
    def test_full_row(self):
        raw = {
            "id": "123456",
            "page_id": "789",
            "page_name": "Test Page",
            "ad_creative_bodies": ["Ad text here"],
            "ad_snapshot_url": "https://facebook.com/ads/archive/...",
            "ad_creative_link_captions": ["example.com"],
            "ad_creative_link_titles": ["Click here"],
            "ad_delivery_start_time": "2024-01-15T00:00:00+0000",
        }
        row = normalize_ad_row(raw, now_iso=NOW)

        assert row["ad_id"] == "123456"
        assert row["page_id"] == "789"
        assert row["page_name"] == "Test Page"
        assert row["ad_text"] == "Ad text here"
        assert row["snapshot_url"] == "https://facebook.com/ads/archive/..."
        assert row["image_url"] is None
        assert "link_caption" not in row  # not persisted (table lacks column)
        assert "link_title" not in row
        assert row["start_date"] == "2024-01-15"
        assert row["last_seen"] == NOW
        assert row["is_active"] is True

    def test_missing_fields(self):
        row = normalize_ad_row({}, now_iso=NOW)

        assert row["ad_id"] == ""
        assert row["page_id"] == ""
        assert row["page_name"] is None
        assert row["ad_text"] is None
        assert row["snapshot_url"] is None
        assert row["image_url"] is None
        assert "link_caption" not in row
        assert "link_title" not in row
        assert row["start_date"] is None

    def test_none_values(self):
        raw = {
            "id": None,
            "page_id": None,
            "page_name": None,
            "ad_creative_bodies": None,
            "ad_snapshot_url": None,
            "ad_creative_link_captions": None,
            "ad_creative_link_titles": None,
            "ad_delivery_start_time": None,
        }
        row = normalize_ad_row(raw, now_iso=NOW)

        assert row["ad_id"] == ""
        assert row["page_name"] is None
        assert row["ad_text"] is None
        assert "link_caption" not in row

    def test_whitespace_page_name(self):
        raw = {"id": "1", "page_id": "2", "page_name": "   "}
        row = normalize_ad_row(raw, now_iso=NOW)
        assert row["page_name"] is None


class TestUtcNowIso:
    def test_returns_string(self):
        result = utc_now_iso()
        assert isinstance(result, str)
        assert "T" in result
