import asyncio

class asyncio_event:
    _cb = {}
    def __init__(self):
        pass
    def register(self, name, func):
        if name not in self._cb:
            self._cb[name] = []

        self._cb[name].append({'func': func})

    async def emit(self, name, args):
        if name in self._cb:
            for each in self._cb[name]:
                #asyncio.get_event_loop().call_soon(each['func'], args)
                task = asyncio.create_task(each['func'](args))
                await task

