from .base_storage import BaseStorage
from ..models.assistant import Assistant
from ..models.thread import Thread
from ..models.message import Message
from ..models.run import Run
from typing import Dict, List, Optional


class MemoryStorage(BaseStorage):
    def __init__(self):
        self.assistants: Dict[str, Assistant] = {}
        self.threads: Dict[str, Thread] = {}
        self.messages: Dict[str, List[Message]] = {}
        self.runs: Dict[str, Run] = {}

    async def save_assistant(self, assistant: Assistant) -> None:
        self.assistants[assistant.id] = assistant

    async def get_assistant(self, assistant_id: str) -> Optional[Assistant]:
        return self.assistants.get(assistant_id)

    async def save_thread(self, thread: Thread) -> None:
        self.threads[thread.id] = thread

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        return self.threads.get(thread_id)

    async def save_message(self, thread_id: str, message: Message) -> None:
        if thread_id not in self.messages:
            self.messages[thread_id] = []
        self.messages[thread_id].append(message)

    async def get_messages(self, thread_id: str) -> List[Message]:
        return self.messages.get(thread_id, [])

    async def save_run(self, run: Run) -> None:
        self.runs[run.id] = run

    async def get_run(self, run_id: str) -> Optional[Run]:
        return self.runs.get(run_id)
