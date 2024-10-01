from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.assistant import Assistant
from ..models.thread import Thread
from ..models.message import Message
from ..models.run import Run


class BaseStorage(ABC):
    @abstractmethod
    async def save_assistant(self, assistant: Assistant) -> None:
        pass

    @abstractmethod
    async def get_assistant(self, assistant_id: str) -> Optional[Assistant]:
        pass

    @abstractmethod
    async def save_thread(self, thread: Thread) -> None:
        pass

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        pass

    @abstractmethod
    async def save_message(self, thread_id: str, message: Message) -> None:
        pass

    @abstractmethod
    async def get_messages(self, thread_id: str) -> List[Message]:
        pass

    @abstractmethod
    async def save_run(self, run: Run) -> None:
        pass

    @abstractmethod
    async def get_run(self, run_id: str) -> Optional[Run]:
        pass
