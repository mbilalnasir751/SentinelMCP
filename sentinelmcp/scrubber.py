import re
import math
from dataclasses import dataclass, field

@dataclass
class ScrubResult:
    cleaned_text:     str
    secrets_found:    int
    patterns_matched: list = field(default_factory=list)

PATTERNS = {
    "aws_access_key":     re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key":     re.compile(r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]"),
    "private_key_header": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "jwt_token":          re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "generic_api_key":    re.compile(r"(?i)(api_key|apikey|api-key)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?"),
    "dotenv_secret":      re.compile(r"(?i)(secret|password|passwd|token)\s*=\s*\S+"),
    "github_token":       re.compile(r"gh[pousr]_[A-Za-z0-9]{36}"),
    "stripe_key":         re.compile(r"sk_(live|test)_[A-Za-z0-9]{24,}"),
}

REDACT           = "[REDACTED]"
ENTROPY_THRESHOLD = 4.2
MIN_ENTROPY_LEN  = 20

def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in freq.values()
    )

def is_high_entropy_secret(token: str) -> bool:
    if len(token) < MIN_ENTROPY_LEN:
        return False
    return shannon_entropy(token) > ENTROPY_THRESHOLD

def scrub(text: str) -> ScrubResult:
    matched = []
    cleaned = text

    for name, pattern in PATTERNS.items():
        if pattern.search(cleaned):
            matched.append(name)
            cleaned = pattern.sub(REDACT, cleaned)

    words = cleaned.split()
    entropy_cleaned = []
    for word in words:
        stripped = word.strip("\"'`,;:")
        if is_high_entropy_secret(stripped):
            matched.append(f"high_entropy:{stripped[:6]}...")
            entropy_cleaned.append(word.replace(stripped, REDACT))
        else:
            entropy_cleaned.append(word)
    cleaned = " ".join(entropy_cleaned)

    return ScrubResult(
        cleaned_text=cleaned,
        secrets_found=len(matched),
        patterns_matched=matched,
    )