from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from app.supabase_store import (
    _INACTIVE_CHUNK,
    _UPSERT_CHUNK,
    fetch_active_ad_ids_for_pages,
    mark_ads_inactive,
    upsert_ads,
)


def _mock_client() -> MagicMock:
    """Crea un mock de supabase.Client con la interfaz fluent de table()."""
    client = MagicMock()
    return client


def _fluent_chain(client: MagicMock, method_chain: list[str]) -> MagicMock:
    """Retorna el último mock de la cadena fluent."""
    obj = client.table.return_value
    for method in method_chain:
        obj = getattr(obj, method).return_value
    return obj


# ── upsert_ads ───────────────────────────────────────────


class TestUpsertAds:
    def test_empty_rows(self):
        client = _mock_client()
        errors = upsert_ads(client, [])
        assert errors == 0
        client.table.assert_not_called()

    def test_single_chunk(self):
        client = _mock_client()
        rows = [{"ad_id": str(i)} for i in range(10)]

        errors = upsert_ads(client, rows)

        assert errors == 0
        client.table.assert_called_with("anuncios_competencia")
        upsert_call = client.table.return_value.upsert
        upsert_call.assert_called_once_with(rows, on_conflict="ad_id")

    def test_multiple_chunks(self):
        client = _mock_client()
        rows = [{"ad_id": str(i)} for i in range(_UPSERT_CHUNK + 50)]

        errors = upsert_ads(client, rows)

        assert errors == 0
        upsert_call = client.table.return_value.upsert
        assert upsert_call.call_count == 2
        first_chunk = upsert_call.call_args_list[0][0][0]
        second_chunk = upsert_call.call_args_list[1][0][0]
        assert len(first_chunk) == _UPSERT_CHUNK
        assert len(second_chunk) == 50

    def test_partial_failure_continues(self):
        client = _mock_client()
        rows = [{"ad_id": str(i)} for i in range(_UPSERT_CHUNK + 50)]

        # First chunk raises, second succeeds
        upsert_mock = client.table.return_value.upsert
        upsert_mock.return_value.execute.side_effect = [
            Exception("DB error"),
            MagicMock(),
        ]

        errors = upsert_ads(client, rows)

        assert errors == 1
        assert upsert_mock.call_count == 2  # both chunks attempted


# ── fetch_active_ad_ids_for_pages ────────────────────────


class TestFetchActiveAdIds:
    def test_empty_page_ids(self):
        client = _mock_client()
        result = fetch_active_ad_ids_for_pages(client, [])
        assert result == {}

    def test_returns_grouped_by_page(self):
        client = _mock_client()

        resp = MagicMock()
        resp.data = [
            {"ad_id": "a1", "page_id": "p1"},
            {"ad_id": "a2", "page_id": "p1"},
            {"ad_id": "a3", "page_id": "p2"},
        ]

        chain = client.table.return_value.select.return_value
        chain = chain.in_.return_value.eq.return_value.range.return_value
        chain.execute.return_value = resp

        result = fetch_active_ad_ids_for_pages(client, ["p1", "p2"])

        assert result["p1"] == {"a1", "a2"}
        assert result["p2"] == {"a3"}


# ── mark_ads_inactive ───────────────────────────────────


class TestMarkAdsInactive:
    def test_empty_list(self):
        client = _mock_client()
        mark_ads_inactive(client, [])
        client.table.assert_not_called()

    def test_marks_inactive(self):
        client = _mock_client()
        ad_ids = ["a1", "a2", "a3"]

        mark_ads_inactive(client, ad_ids)

        client.table.assert_called_with("anuncios_competencia")
        update_call = client.table.return_value.update
        update_call.assert_called_once_with({"is_active": False})

    def test_multiple_chunks(self):
        client = _mock_client()
        ad_ids = [f"a{i}" for i in range(_INACTIVE_CHUNK + 10)]

        mark_ads_inactive(client, ad_ids)

        in_call = client.table.return_value.update.return_value.in_
        assert in_call.call_count == 2
