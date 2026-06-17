from sentinelmcp.scrubber import scrub, shannon_entropy, is_high_entropy_secret

# ── Shannon entropy tests ──

def test_entropy_low_for_simple_string():
    assert shannon_entropy("aaaaaaaaaa") < 1.0

def test_entropy_high_for_random_string():
    assert shannon_entropy("aB3$xK9!mZ2@qW7#") > 3.5

def test_entropy_empty_string():
    assert shannon_entropy("") == 0.0

# ── High entropy secret detection ──

def test_high_entropy_secret_detected():
    # This looks like a real random secret
    assert is_high_entropy_secret("wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY") is True

def test_short_string_not_flagged():
    # Too short to be a secret even if high entropy
    assert is_high_entropy_secret("aB3$xK") is False

def test_low_entropy_not_flagged():
    # Long but repetitive — not a secret
    assert is_high_entropy_secret("aaaaaaaaaaaaaaaaaaaaaaaaa") is False

# ── AWS key pattern ──

def test_aws_access_key_redacted():
    text = "My key is AKIAIOSFODNN7EXAMPLE please use it"
    result = scrub(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in result.cleaned_text
    assert "[REDACTED]" in result.cleaned_text
    assert result.secrets_found >= 1

def test_aws_key_pattern_counted():
    text = "key=AKIAIOSFODNN7EXAMPLE"
    result = scrub(text)
    assert "aws_access_key" in result.patterns_matched

# ── JWT token pattern ──

def test_jwt_token_redacted():
    fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    result = scrub(f"Authorization: Bearer {fake_jwt}")
    assert fake_jwt not in result.cleaned_text
    assert result.secrets_found >= 1

# ── GitHub token pattern ──

def test_github_token_redacted():
    text = "token: ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"
    result = scrub(text)
    assert "ghp_" not in result.cleaned_text
    assert result.secrets_found >= 1

# ── Private key header ──

def test_private_key_header_redacted():
    text = "-----BEGIN RSA PRIVATE KEY----- MIIEowIBAAKCAQEA..."
    result = scrub(text)
    assert "BEGIN RSA PRIVATE KEY" not in result.cleaned_text
    assert result.secrets_found >= 1

# ── Clean text untouched ──

def test_clean_text_not_modified():
    text = "Hello, can you help me write a Python function?"
    result = scrub(text)
    assert result.cleaned_text == text
    assert result.secrets_found == 0

def test_clean_text_secrets_found_zero():
    result = scrub("What is the capital of France?")
    assert result.secrets_found == 0
    assert result.patterns_matched == []

# ── Multiple secrets in one payload ──

def test_multiple_secrets_counted():
    text = (
        "AWS key: AKIAIOSFODNN7EXAMPLE "
        "GitHub: ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"
    )
    result = scrub(text)
    assert result.secrets_found >= 2
    assert "[REDACTED]" in result.cleaned_text