from collections import defaultdict, deque
from typing import List, Optional

class ShortTermMemory:
    def __init__(self, max_len: int = 4):
        self.max_len = max_len
        self.store = defaultdict(lambda: deque(maxlen=max_len))

    def add(self, session_id: str, text: str):
        self.store[session_id].append(text)

    def get_recent(self, session_id: Optional[str] = None) -> List[str]:
        if session_id is None:
            return []
        return list(self.store[session_id])