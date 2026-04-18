from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.config import Settings
from app.meta_archive_client import (
    MetaArchiveError,
    _is_rate_limit_error,
    _request_json_with_retries,
    iter_ads_archive,
)

SETTINGS = Settings(
    supabase_url="https://test.supabase.co",
    supabase_key="test-key",
    facebook_access_token="test-token",
    meta_max_retries=3,
    meta_initial_backoff_seconds=0.01,  # fast tests
)


# ── _is_rate_limit_error ─────────────────────────────────


class TestIsRateLimitError:
    def test_rate_limit_code(self):
        assert _is_rate_limit_error({"error": {"code": 4}}) is True
        assert _is_rate_limit_error({"error": {"code": 17}}) is True
        assert _is_rate_limit_error({"error": {"code": 80000}}) is True

    def test_rate_limit_subcode(self):
        assert _is_rate_limit_error({"error": {"code": 999, "error_subcode": 2446079}}) is True

    def test_rate_limit_message(self):
        assert _is_rate_limit_error({"error": {"code": 999, "message": "Too Many requests"}}) is True
        assert _is_rate_limit_error({"error": {"code": 999, "message": "request limit reached"}}) is True

    def test_not_rate_limit(self):
        assert _is_rate_limit_error({"error": {"code": 100, "message": "Invalid param"}}) is False

    def test_no_error_key(self):
        assert _is_rate_limit_error({}) is False


# ── _request_json_with_retries ───────────────────────────


class TestRequestJsonWithRetries:
    def _mock_session(self, responses: list[MagicMock]) -> MagicMock:
        session = MagicMock(spec=requests.Session)
        session.request = MagicMock(side_effect=responses)
        return session

    def _json_response(self, data: dict, status: int = 200) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = data
        resp.text = json.dumps(data)
        return resp

    def test_success_first_try(self):
        session = self._mock_session([self._json_response({"data": []})])
        result = _request_json_with_retries(
            SETTINGS, session, method="GET", url="https://example.com", params={}
        )
        assert result == {"data": []}
        assert session.request.call_count == 1

    def test_retries_on_rate_limit_then_succeeds(self):
        rate_limit_resp = self._json_response(
            {"error": {"code": 4, "message": "rate limit"}}, status=429
        )
        ok_resp = self._json_response({"data": ["ok"]})
        session = self._mock_session([rate_limit_resp, ok_resp])

        result = _request_json_with_retries(
            SETTINGS, session, method="GET", url="https://example.com"
        )
        assert result == {"data": ["ok"]}
        assert session.request.call_count == 2

    def test_raises_after_max_retries(self):
        error_resp = self._json_response(
            {"error": {"code": 4, "message": "rate limit"}}, status=429
        )
        session = self._mock_session([error_resp] * 3)

        with pytest.raises(MetaArchiveError, match="Falló la petición tras reintentos"):
            _request_json_with_retries(
                SETTINGS, session, method="GET", url="https://example.com"
            )
        assert session.request.call_count == 3

    def test_retries_on_http_429(self):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        ok_resp = self._json_response({"data": []})
        session = self._mock_session([resp_429, ok_resp])

        result = _request_json_with_retries(
            SETTINGS, session, method="GET", url="https://example.com"
        )
        assert result == {"data": []}

    def test_retries_on_connection_error(self):
        ok_resp = self._json_response({"data": []})
        session = MagicMock(spec=requests.Session)
        session.request = MagicMock(
            side_effect=[requests.ConnectionError("fail"), ok_resp]
        )

        result = _request_json_with_retries(
            SETTINGS, session, method="GET", url="https://example.com"
        )
        assert result == {"data": []}

    def test_non_rate_limit_api_error_raises_immediately(self):
        """Non-rate-limit API errors still retry (caught by except block)."""
        error_resp = self._json_response(
            {"error": {"code": 100, "message": "Invalid parameter"}}, status=400
        )
        session = self._mock_session([error_resp] * 3)

        with pytest.raises(MetaArchiveError):
            _request_json_with_retries(
                SETTINGS, session, method="GET", url="https://example.com"
            )


# ── iter_ads_archive ─────────────────────────────────────


class TestIterAdsArchive:
    @patch("app.meta_archive_client._request_json_with_retries")
    def test_single_page(self, mock_req):
        mock_req.return_value = {
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {},
        }

        ads = list(iter_ads_archive(SETTINGS, ["page1"]))
        assert len(ads) == 2
        assert ads[0]["id"] == "1"

    @patch("app.meta_archive_client._request_json_with_retries")
    def test_pagination_via_next_url(self, mock_req):
        mock_req.side_effect = [
            {
                "data": [{"id": "1"}],
                "paging": {"next": "https://graph.facebook.com/next-page"},
            },
            {
                "data": [{"id": "2"}],
                "paging": {},
            },
        ]

        ads = list(iter_ads_archive(SETTINGS, ["page1"]))
        assert len(ads) == 2
        assert mock_req.call_count == 2

    @patch("app.meta_archive_client._request_json_with_retries")
    def test_pagination_via_cursor(self, mock_req):
        mock_req.side_effect = [
            {
                "data": [{"id": "1"}],
                "paging": {"cursors": {"after": "cursor123"}},
            },
            {
                "data": [{"id": "2"}],
                "paging": {},
            },
        ]

        ads = list(iter_ads_archive(SETTINGS, ["page1"]))
        assert len(ads) == 2

    @patch("app.meta_archive_client._request_json_with_retries")
    def test_empty_response(self, mock_req):
        mock_req.return_value = {"data": [], "paging": {}}

        ads = list(iter_ads_archive(SETTINGS, ["page1"]))
        assert ads == []
