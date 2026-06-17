import pytest
from app import config


def test_valid_airports_contains_known_codes():
    assert "ARN" in config.VALID_AIRPORTS
    assert "GOT" in config.VALID_AIRPORTS
    assert len(config.VALID_AIRPORTS) == 12


def test_base_url():
    assert config.SWEDAVIA_BASE_URL == "https://api.swedavia.se/flightinfo/v2"


def test_airport_names_cover_all_valid_airports():
    for code in config.VALID_AIRPORTS:
        assert code in config.AIRPORT_NAMES
        assert config.AIRPORT_NAMES[code].strip()


def test_get_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("SWEDAVIA_API_KEY", "test-key-123")
    assert config.get_api_key() == "test-key-123"


def test_get_api_key_missing_raises(monkeypatch):
    monkeypatch.delenv("SWEDAVIA_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SWEDAVIA_API_KEY"):
        config.get_api_key()
