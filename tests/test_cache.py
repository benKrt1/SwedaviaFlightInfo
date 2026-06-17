from app.cache import TTLCache


def test_set_then_get_returns_value():
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", [1, 2, 3])
    assert cache.get("k") == [1, 2, 3]


def test_get_missing_returns_none():
    cache = TTLCache(ttl_seconds=60)
    assert cache.get("nope") is None


def test_expired_entry_returns_none():
    fake_time = {"now": 1000.0}
    cache = TTLCache(ttl_seconds=60, time_fn=lambda: fake_time["now"])
    cache.set("k", "v")
    fake_time["now"] = 1061.0  # 61s later, past TTL
    assert cache.get("k") is None


def test_not_yet_expired_returns_value():
    fake_time = {"now": 1000.0}
    cache = TTLCache(ttl_seconds=60, time_fn=lambda: fake_time["now"])
    cache.set("k", "v")
    fake_time["now"] = 1059.0  # 59s later, within TTL
    assert cache.get("k") == "v"
