from sentinelmcp.circuit_breaker import CircuitBreaker, get_breaker, reset_breaker

# ── Hash computation ──

def test_same_payload_produces_same_hash():
    cb = CircuitBreaker()
    payload = {
        "model": "claude-sonnet-4-6",
        "messages": [{"role": "user", "content": "hello"}]
    }
    hash1 = cb.compute_hash(payload)
    hash2 = cb.compute_hash(payload)
    assert hash1 == hash2

def test_different_payload_produces_different_hash():
    cb = CircuitBreaker()
    payload1 = {"model": "claude-sonnet-4-6", "messages": [{"role": "user", "content": "hello"}]}
    payload2 = {"model": "claude-sonnet-4-6", "messages": [{"role": "user", "content": "goodbye"}]}
    assert cb.compute_hash(payload1) != cb.compute_hash(payload2)

def test_empty_payload_hashes_without_error():
    cb = CircuitBreaker()
    result = cb.compute_hash({})
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest length

# ── Circuit breaker logic ──

def test_no_trip_on_first_request():
    cb = CircuitBreaker()
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    assert cb.check(payload) is False

def test_no_trip_below_threshold():
    cb = CircuitBreaker(window_size=5, threshold=3)
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    cb.check(payload)
    cb.check(payload)
    # Two identical requests — threshold is 3, should not trip yet
    assert cb.tripped is False

def test_trips_at_threshold():
    cb = CircuitBreaker(window_size=5, threshold=3)
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    cb.check(payload)
    cb.check(payload)
    result = cb.check(payload)
    # Third identical request — should trip
    assert result is True
    assert cb.tripped is True

def test_stays_tripped_after_threshold():
    cb = CircuitBreaker(window_size=5, threshold=3)
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    for _ in range(5):
        cb.check(payload)
    assert cb.tripped is True

def test_different_requests_do_not_trip():
    cb = CircuitBreaker(window_size=5, threshold=3)
    for i in range(10):
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": f"message {i}"}]
        }
        cb.check(payload)
    assert cb.tripped is False

# ── Reset logic ──

def test_reset_clears_trip():
    cb = CircuitBreaker(window_size=5, threshold=3)
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    for _ in range(3):
        cb.check(payload)
    assert cb.tripped is True
    cb.reset()
    assert cb.tripped is False

def test_reset_clears_history():
    cb = CircuitBreaker(window_size=5, threshold=3)
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    cb.check(payload)
    cb.check(payload)
    cb.reset()
    assert len(cb.history) == 0

# ── Session management ──

def test_different_sessions_are_independent():
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    breaker_a = get_breaker("session_a")
    breaker_b = get_breaker("session_b")
    for _ in range(3):
        breaker_a.check(payload)
    assert breaker_a.tripped is True
    assert breaker_b.tripped is False

def test_reset_breaker_by_session_id():
    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}
    breaker = get_breaker("session_reset_test")
    for _ in range(3):
        breaker.check(payload)
    assert breaker.tripped is True
    reset_breaker("session_reset_test")
    assert breaker.tripped is False