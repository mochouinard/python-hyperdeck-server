#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pip3 install websockets
# pip3 install aiohttp
import asyncio

import websockets

import aiohttp
import async_timeout
from aiohttp import web

from hdinterface import HyperDeckInterface

import re
import os
import json

class WS:
    def __init__(self, hdi):
        self.hdi = hdi
    async def handler(self, websocket, path):
        while True:
            response = {'error': 'unknown command'}
            try:
                data = await websocket.recv()
                print(f"< {data}")
                j = json.loads(data)
                if j['cmd'] == 'load_list':
                    response = {'type': 'media_list', 'list': self.hdi.list_media()}
                elif j['cmd'] == 'delete_media':
                    if j['filename'] in self.hdi.list_media():
                        os.remove("videos/" + j['filename'])
                        response = {'type': 'media_removed', 'filename': j['filename']}
                        await self.hdi.refreshMedia()

                    else:
                        response = {'error': 'Invalid filename'}
                print (response)
                await websocket.send(json.dumps(response))
            except websockets.exceptions.ConnectionClosed:
                print(f'{websocket.remote_address} lost connection')
                return

# HTTP:
class HTTP:
    def __init__(self, hdi):
        self.hdi = hdi

    async def index_handle(self, request):
        return web.FileResponse('html/index.html')
        #name = request.match_info.get('name', "Anonymous")
        #text = "Hello, " + name
        return web.Response(text=text)

    async def send(self, writer, arr):
        out = ""
        for item in arr:
            out += item + "\r\n"

        out += "\r\n"
        response = bytes(out, 'ascii')
        writer.write(response)
        await writer.drain()

    async def store_fileupload_handler(self, request):

        reader = await request.multipart()

        # /!\ Don't forget to validate your inputs /!\

        # reader.next() will `yield` the fields of your form
        while True:
            part = await reader.next()
            if part is None:
                break
            print(part.headers)
            filename = part.filename
            # You cannot rely on Content-Length if transfer is chunked.
            size = 0
            with open(os.path.join('videos/', filename), 'wb') as f:
                while True:
                    chunk = await part.read_chunk()  # 8192 bytes by default.
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)
        await self.hdi.refreshMedia()
        return web.Response(text='{} sized of {} successfully stored'
                             ''.format(filename, size))
# HyperDeck Server
class HDClient:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
    def genResponse(self, response):
        out = ""
        qty = 0
        for item in response:
            if isinstance(item, list):
                for subitem in item:
                    out += subitem + "\r\n"
                    qty += 1
            else:
                out += item + "\r\n"
                qty += 1
        if qty > 1:
            out += "\r\n"
        return out

    async def send(self, msg):
        data = self.genResponse(msg)
        response = bytes(data, 'ascii')
        self.writer.write(response)
        await self.writer.drain()

class HDServer:

    def __init__(self, hdi):
        self._clients = set()
        self.hdi = hdi
        self.hdi.registerEvent('newmedia', self.notifySlotChange)

    async def send_to_all(self, msg) -> None:
        if self._clients:
            await asyncio.wait([client.send(msg) for client in self._clients])

    async def notifySlotChange(self, args):
        response = [
                "502 slot info:",
                self.hdi.buildSlotInfo(2)
                ]
        await self.send_to_all(response)

    def parseArg(self, arg):
        return re.findall('([a-zA-Z][^:]+): ([^ ]+)', arg)
    def parseArgGet(self, params, field):
        if params:
            for arg in params:
                (param, val) = arg
                if param == field:
                    return val
        return None

    def parseLineGet(self, lines, field):
        for line in lines:
            s = line.strip().split(':', 1)
            if s[0] == field:
                return s[1].strip()
        return None

    def parseGet(self, args, lines, field):
        res = self.parseArgGet(args, field)
        if not res:
            res = self.parseLineGet(lines, field)
        print("XXXXXX", field, res)
        return res

    async def new_conn(self, reader, writer):
        client = HDClient(reader, writer)
        self._clients.add(client)

        await client.send([
                    "500 connection info:",
                    "protocol version: 1.6",
                    "model: Python Hyperdeck Server"
                    ])

        while not reader.at_eof() and not writer.is_closing():
            response = ["100 syntax error"]
            data = await reader.read(1500)
            message = str(data, 'ascii')
            addr = writer.get_extra_info('peername')

            print(f"Received {message!r} from {addr!r}")

            lines = message.split('\n')
            data = lines[0]
            s = data.strip().split(":", 1)
            cmd = s[0]
            if len(s) > 1 and s[1]:
                params = self.parseArg(s[1].strip())
            else:
                params = None

            if cmd == 'play':
                self.hdi.hd.play()
                rate = self.parseGet(params, lines, 'speed')
                if rate:
                    rate = int(rate)
                    if rate == 0:
                        self.hdi.hd.pause()
                    self.hdi.hd.set_rate(rate/100)
                    response = ["200 ok"]
            elif cmd == 'stop':
                self.hdi.hd.pause()
                response = ["200 ok"]
            elif cmd == 'goto':
                clip_id = self.parseGet(params, lines, 'clip id')
                if clip_id:
                    if clip_id[:1] == '+':
                        clip_id = self.hdi.hd.ActiveClip() + int(val[1:])
                    elif clip_id[:1] == '-':
                        clip_id = self.hdi.hd.ActiveClip() - int(val[1:])
                    else:
                        clip_id = int(clip_id)
                    self.hdi.load_clip(clip_id)
                    response = ["200 ok"]
                else:
                    response = ["100 syntax error"]
            elif cmd == 'slot info':
                slot_id = self.parseGet(params, lines, 'slot id')
                if slot_id:
                    response = [
                                "202 slot info:",
                                self.hdi.buildSlotInfo(int(slot_id))
                                ]
            elif cmd == 'clips count':
                fl = self.hdi.list_media()
                response = [
                        "214 clips count:",
                        "clip count: " + str(len(fl))
                        ]
            elif cmd == 'clips get':
                clip_id = self.parseGet(params, lines, 'clip id')
                response = [ 
                            "205 clips info:"
                            ]
                fl = self.hdi.list_media()
                at = 1

                if clip_id:
                    clip_id = int(clip_id)
                    fl = [fl[clip_id-1]]
                    at = clip_id
                else:
                    response.append("clip count: " + str(len(fl)))
                for f in fl:
                    (width, height, duration, fps, fps_out) = (0,0,0,0,24)
                    meta = self.hdi.findClipMetadata(at)
                    if meta:
                        (width, height, duration, fps) = meta
                        if fps != 0 and fps != "0/0":
                            print ("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII", fps)
                            fps_s = fps.split('/')
                            fps_out = int(fps_s[0]) / int(fps_s[1])
                        else:
                            fps_out = 24
                            duration = 1000
                    (h,m,s,fr) = self.hdi.hd.time_to_timecode(duration, fps_out)
                    tc = f'{h:02}:{m:02}:{s:02}:{fr:02}'
                    #f = 'video' + str(at) + '.mp4'
                    response.append(str(at) + ":  " + f + " 00:00:00:00 " + tc)
                    at += 1
            elif cmd == 'remote':
                response = [
                    "210 remote info:",
                    self.hdi.buildRemote()
                    ]
            elif cmd == 'transport info':
                response = [
                        "208 transport info:",
                        self.hdi.buildTransportInfo()
                        ]
            elif cmd == 'notify':
                response = ["200 ok"]

            await client.send(response)
            print(f"Send: {response!r}")

        print("Close the connection")
        writer.close()
        self._clients.remove(client)

import logging
async def serve():                                                                                           
    # Telnet
    hdi = HyperDeckInterface()

    hds = HDServer(hdi)
    ts = await asyncio.start_server( hds.new_conn, '', 9993)
  
    addr = ts.sockets[0].getsockname()
    print(f'Serving HyperDeck Server on {addr}')

    
    logging.basicConfig(level=logging.DEBUG)
    #http
    http = HTTP(hdi)
    app = aiohttp.web.Application()
    # index, loaded for all application uls.
    app.router.add_get('/', http.index_handle)
    app.router.add_post('/upload', http.store_fileupload_handler)
    app.router.add_static('/videos/', path='videos/', name='static')
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, '', '8082')
    await site.start()

    #ws
    ws = WS(hdi)
    wsserver = await websockets.serve(ws.handler, '', 8765)
    await wsserver.wait_closed()



asyncio.run(serve())
#asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
