import hashlib
import json
import os
from collections import deque
from dataclasses import dataclass, field

WINDOW_SIZE = int(os.getenv("LOOP_WINDOW_SIZE", 5))
THRESHOLD   = int(os.getenv("LOOP_THRESHOLD", 3))

@dataclass
class CircuitBreaker:
    window_size: int   = WINDOW_SIZE
    threshold:   int   = THRESHOLD
    history:     deque = field(default_factory=lambda: deque(maxlen=WINDOW_SIZE))
    tripped:     bool  = False

    def compute_hash(self, payload: dict) -> str:
        stable = {
            "model": payload.get("model", ""),
            "tools": sorted([
                t.get("name", "") for t in payload.get("tools", [])
            ]),
            "messages": [
                {
                    "role":    m.get("role", ""),
                    "content": str(m.get("content", ""))[:120]
                }
                for m in payload.get("messages", [])[-3:]
            ],
        }
        raw = json.dumps(stable, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def check(self, payload: dict) -> bool:
        if self.tripped:
            return True
        state_hash = self.compute_hash(payload)
        self.history.append(state_hash)
        duplicate_count = sum(1 for h in self.history if h == state_hash)
        if duplicate_count >= self.threshold:
            self.tripped = True
            return True
        return False

    def reset(self):
        self.history.clear()
        self.tripped = False

_breakers: dict[str, CircuitBreaker] = {}

def get_breaker(session_id: str) -> CircuitBreaker:
    if session_id not in _breakers:
        _breakers[session_id] = CircuitBreaker()
    return _breakers[session_id]

def reset_breaker(session_id: str):
    if session_id in _breakers:
        _breakers[session_id].reset()