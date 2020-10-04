import asyncio
import functools

class asyncio_event:
    _cb = {}
    def __init__(self):
        self.loop = asyncio.get_event_loop()
    def register(self, name, func):
        if name not in self._cb:
            self._cb[name] = []

        self._cb[name].append({'func': func})

    def emitX(self, name, args):
        #self.loop.call_soon_threadsafe( functools.partial(self.emit, name, args));
        future = asyncio.run_coroutine_threadsafe(self.emit(name, args), self.loop)
        #future = asyncio.run_coroutine_threadsafe(self.test(), self.loop)
        #print(future.running())
        #print(future.running())
        #print(future.running())

        #print(future.result())
    async def emit(self, name, args):
        if name in self._cb:
            for each in self._cb[name]:
                #asyncio.get_event_loop().call_soon(each['func'], args)
                task = asyncio.create_task(each['func'](args))
                await task
        return "XXX"

