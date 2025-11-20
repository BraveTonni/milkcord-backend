import logging

from abc import ABC, abstractmethod

from src.schemas.ws import WSConnection

from src.ws.connection_manager import WSConnectionManager


class EventHandler(ABC):
    def __init__(self, connection: WSConnection, manager: WSConnectionManager):
        self.connection = connection
        self.manager = manager

        self._logger = logging.getLogger(__name__)

    @abstractmethod
    async def handle(self, content: dict) -> None:
        raise NotImplementedError()
