from collections import defaultdict, deque
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ShortTermMemory:
    def __init__(self, max_len: int = 4):
        self.max_len = max_len
        self.store = defaultdict(lambda: deque(maxlen=max_len))
        logger.debug("ShortTermMemory initialized max_len=%d", max_len)

    def add(self, session_id: str, text: str):
        logger.debug("Memory add session_id=%s, text_len=%d", session_id, len(text or ""))
        self.store[session_id].append(text)

    def get_recent(self, session_id: Optional[str] = None) -> List[str]:
        if session_id is None:
            logger.debug("get_recent called with session_id=None")
            return []
        entries = list(self.store[session_id])
        logger.debug("get_recent session_id=%s, count=%d", session_id, len(entries))
        return entries