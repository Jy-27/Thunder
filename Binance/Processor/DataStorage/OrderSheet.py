from enum import Enum
from typing import Optional, List, Dict


class OrderSheet(Enum):
    market:Optional[str] = None
    symbol:Optional[str] = None
    