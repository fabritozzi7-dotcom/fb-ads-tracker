from __future__ import annotations

import json
import textwrap

import pytest

from app.csv_client import CsvImportError, iter_ads_from_csv


@pytest.fixture
def csv_file(tmp_path):
    """Crea un CSV temporal con datos de prueba."""
    content = textwrap.dedent("""\
        ad_id,page_id,page_name,ad_text,snapshot_url,start_date
        101,P1,Página Test,"Texto del anuncio",https://example.com/snap,2024-01-15
        102,P1,Página Test,"Segundo anuncio",https://example.com/snap2,2024-02-01
    """)
    f = tmp_path / "test.csv"
    f.write_text(content, encoding="utf-8")
    return f


@pytest.fixture
def csv_with_optional(tmp_path):
    """CSV con columnas opcionales."""
    content = textwrap.dedent("""\
        ad_id,page_id,page_name,ad_text,snapshot_url,start_date,link_caption,link_title
        201,P2,Otra Página,"Ad text",https://example.com,2024-03-01,example.com,Click here
    """)
    f = tmp_path / "optional.csv"
    f.write_text(content, encoding="utf-8")
    return f


@pytest.fixture
def json_file(tmp_path):
    """Crea un JSON temporal con datos en formato API."""
    data = [
        {
            "id": "301",
            "page_id": "P3",
            "page_name": "JSON Page",
            "ad_creative_bodies": ["JSON ad text"],
            "ad_snapshot_url": "https://example.com/snap3",
            "ad_delivery_start_time": "2024-04-01T00:00:00+0000",
        }
    ]
    f = tmp_path / "test.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


@pytest.fixture
def json_with_data_key(tmp_path):
    """JSON con estructura {data: [...]}."""
    data = {
        "data": [
            {
                "id": "401",
                "page_id": "P4",
                "page_name": "Wrapped Page",
                "ad_creative_bodies": ["Wrapped text"],
                "ad_snapshot_url": "https://example.com/snap4",
                "ad_delivery_start_time": "2024-05-01",
            }
        ]
    }
    f = tmp_path / "wrapped.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


# ── CSV parsing ──────────────────────────────────────────


class TestIterAdsFromCsv:
    def test_basic_csv(self, csv_file):
        ads = list(iter_ads_from_csv(csv_file))
        assert len(ads) == 2
        assert ads[0]["id"] == "101"
        assert ads[0]["page_id"] == "P1"
        assert ads[0]["ad_creative_bodies"] == ["Texto del anuncio"]
        assert ads[0]["ad_snapshot_url"] == "https://example.com/snap"
        assert ads[0]["ad_delivery_start_time"] == "2024-01-15"

    def test_optional_columns(self, csv_with_optional):
        ads = list(iter_ads_from_csv(csv_with_optional))
        assert len(ads) == 1
        assert ads[0]["ad_creative_link_captions"] == ["example.com"]
        assert ads[0]["ad_creative_link_titles"] == ["Click here"]

    def test_missing_optional_columns(self, csv_file):
        ads = list(iter_ads_from_csv(csv_file))
        assert ads[0]["ad_creative_link_captions"] is None
        assert ads[0]["ad_creative_link_titles"] is None

    def test_semicolon_delimiter(self, tmp_path):
        content = "ad_id;page_id;page_name;ad_text;snapshot_url;start_date\n1;P1;Page;Text;url;2024-01-01\n"
        f = tmp_path / "semi.csv"
        f.write_text(content, encoding="utf-8")
        ads = list(iter_ads_from_csv(f))
        assert len(ads) == 1
        assert ads[0]["id"] == "1"

    def test_bom_encoding(self, tmp_path):
        content = "ad_id,page_id,page_name,ad_text,snapshot_url,start_date\n1,P1,Page,Text,url,2024-01-01\n"
        f = tmp_path / "bom.csv"
        f.write_text(content, encoding="utf-8-sig")  # utf-8-sig adds BOM automatically
        ads = list(iter_ads_from_csv(f))
        assert len(ads) == 1

    def test_empty_ad_text(self, tmp_path):
        content = "ad_id,page_id,page_name,ad_text,snapshot_url,start_date\n1,P1,Page,,url,2024-01-01\n"
        f = tmp_path / "empty_text.csv"
        f.write_text(content, encoding="utf-8")
        ads = list(iter_ads_from_csv(f))
        assert ads[0]["ad_creative_bodies"] is None


# ── JSON parsing ─────────────────────────────────────────


class TestIterAdsFromJson:
    def test_json_list(self, json_file):
        ads = list(iter_ads_from_csv(json_file))
        assert len(ads) == 1
        assert ads[0]["id"] == "301"
        assert ads[0]["page_name"] == "JSON Page"

    def test_json_with_data_key(self, json_with_data_key):
        ads = list(iter_ads_from_csv(json_with_data_key))
        assert len(ads) == 1
        assert ads[0]["id"] == "401"

    def test_json_invalid_format(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text('"just a string"', encoding="utf-8")
        with pytest.raises(CsvImportError, match="Formato JSON no reconocido"):
            list(iter_ads_from_csv(f))

    def test_json_parse_error(self, tmp_path):
        f = tmp_path / "broken.json"
        f.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(CsvImportError, match="Error leyendo JSON"):
            list(iter_ads_from_csv(f))


# ── Error handling ───────────────────────────────────────


class TestCsvErrors:
    def test_file_not_found(self):
        with pytest.raises(CsvImportError, match="Archivo no encontrado"):
            list(iter_ads_from_csv("/nonexistent/file.csv"))

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("", encoding="utf-8")
        with pytest.raises(CsvImportError, match="Archivo vacío"):
            list(iter_ads_from_csv(f))

    def test_missing_columns(self, tmp_path):
        content = "ad_id,page_name\n1,Page\n"
        f = tmp_path / "incomplete.csv"
        f.write_text(content, encoding="utf-8")
        with pytest.raises(CsvImportError, match="Faltan columnas obligatorias"):
            list(iter_ads_from_csv(f))
