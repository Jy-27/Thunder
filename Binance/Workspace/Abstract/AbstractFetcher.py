import asyncio
from abc import ABC, abstractmethod
from typing import Any


class BaseFetcher(ABC):
    @abstractmethod
    async def tasks(self):
        pass
    
    async def start(self):
        pass