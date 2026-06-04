import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel


RunEventQueue = asyncio.Queue[BaseModel | None]


@dataclass
class RunChannel:
    history: list[BaseModel] = field(default_factory=list)
    subscribers: set[RunEventQueue] = field(default_factory=set)
    closed: bool = False


class RunEventBroker:
    def __init__(self) -> None:
        self.channels: dict[UUID, RunChannel] = {}
        self.lock = asyncio.Lock()

    async def publish(
        self,
        run_id: UUID,
        event: BaseModel,
        *,
        terminal: bool = False,
    ) -> None:
        async with self.lock:
            channel = self.channels.setdefault(run_id, RunChannel())
            channel.history.append(event)

            for queue in channel.subscribers:
                queue.put_nowait(event)

            if terminal:
                channel.closed = True
                for queue in channel.subscribers:
                    queue.put_nowait(None)

    async def subscribe(self, run_id: UUID) -> AsyncIterator[BaseModel]:
        queue: RunEventQueue = asyncio.Queue()

        async with self.lock:
            channel = self.channels.setdefault(run_id, RunChannel())

            for event in channel.history:
                queue.put_nowait(event)

            if channel.closed:
                queue.put_nowait(None)
            else:
                channel.subscribers.add(queue)

        try:
            while True:
                event = await queue.get()
                if event is None:
                    return
                yield event
        finally:
            async with self.lock:
                channel.subscribers.discard(queue)


run_event_broker = RunEventBroker()
