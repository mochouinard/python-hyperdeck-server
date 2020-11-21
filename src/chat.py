import asyncio

from asyncio_event import asyncio_event

class Chat:
    _chat = []
    _event = asyncio_event()
    def __init__(self):
        pass
    def add(self, info):
        self._chat.append(info)
        self._event.emitX("chatnew", info)

    def list(self):
        return self._chat
    def registerEvent(self, name, func):
        self._event.register(name, func)

