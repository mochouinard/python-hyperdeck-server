#!/usr/bin/env python3
import vlc
import socket
import threading
import socketserver
import time
import os
import math

import subprocess
import shlex
import json

import re

class HyperDeckPlayer():
    _playing = False 
    _debug = False
    def __init__(self):
        self._instance = vlc.Instance(['--video-on-top'])#, '--start-paused'])
        self._medialist = self._instance.media_list_new()
        self._listplayer = self._instance.media_list_player_new()
        #self._listplayer.set_media_player(player)
        self._player = self._instance.media_player_new()
        self._listplayer.set_media_player(self._player)
        self._player.set_fullscreen(True)
    def time_to_timecode(self, time, fps):
        h = 0
        m = 0
        s = 0
        f = 0
        t = time
        s = t/1000
        if s >= 61:
            m = math.floor(s / 60)
            s -= m * 60
        if m > 60:
            h = math.floor(m / 60)
            m -= h * 60
        (milli, s) = math.modf(s)
        s = int(s)
        f = math.floor(fps * milli)
        return (h,m,s,f)
    def get_time(self):
        return self._player.get_time()
    def get_length(self):
        return self._player.get_length()
    def SongFinished(self, event):
        global finish
        print ("Event reports - finished")
        #self._player.pause()
        #self._player.set_time(30000)
        finish = 1
    def poschanged(self, event):
        #print("poschanged")
        if self._playing == False and self._player.has_vout():
            self._player.pause()

        pass#print(time)
    def ePlaying(self, event):
        if self._debug:
            print("ePlaying")
        if self._playing == False and self._player.has_vout():
            self._player.pause()
        pass#self.is_playing = True
    def eStopped(self, event):
        print("eStopped")
        pass#self.is_playing = False
    def ePaused(self, event):
        if self._debug:
            print("ePaused")
        pass#self.is_playing = False
    def ePausable(self, event):
        if self._playing == False:
            self._player.pause()
        if self._debug:
            print("ePausable")
    def eUncorked(self, event):
        print("eUncorked")
    def eOpening(self, event):
        if self._debug:
            print("eOpening")
    def eBuffering(self, event):
        if self._debug:
            print("eBuffering") #, event.getBuffering())
    def eMediaState(self, event):
        print ("eMedia", self.media.get_state())
    def eVout(self, event):
        if self._debug:
            print ("eVout")
        if self._playing == False and self._player.has_vout():
            self._player.pause()

    def is_playing(self):
        return self._player.is_playing()
    def get_fps(self):
        return self._player.get_fps()
    def get_rate(self):
        return self._player.get_rate()
    def set_rate(self, rate):
        self._player.set_rate(rate)
    def load(self, path):
        self.media = self._instance.media_new(path)
        events = self.media.event_manager()

        events.event_attach(vlc.EventType.MediaStateChanged, self.eMediaState)

        self._player.set_media(self.media)
        #mfps = int(1000 / (self._player.get_fps() or 30))

        #self._player.set_time(1)
        #t = self._player.get_time()
        #print("TIME: ", t)
        #while self._player.get_state() in [vlc.State.Playing, vlc.State.Opening, vlc.State.NothingSpecial]:
        #    self._player.pause()
        #    print(self._player.get_state(), self._player.is_playing())
        #print(self._player.get_state())
        #self._player.set_time(0)
        #self._player.pause()
        print(self._player.get_state())
        #time.sleep(1)
        events = self._player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.SongFinished)
        events.event_attach(vlc.EventType.MediaPlayerPlaying, self.ePlaying)
        events.event_attach(vlc.EventType.MediaPlayerPositionChanged, self.poschanged)
        events.event_attach(vlc.EventType.MediaPlayerStopped, self.eStopped)
        events.event_attach(vlc.EventType.MediaPlayerPaused, self.ePaused)
        events.event_attach(vlc.EventType.MediaPlayerPositionChanged, self.poschanged)
        events.event_attach(vlc.EventType.MediaPlayerPausableChanged, self.ePausable)
        events.event_attach(vlc.EventType.MediaPlayerUncorked, self.eUncorked)
        events.event_attach(vlc.EventType.MediaPlayerVout, self.eVout)
        events.event_attach(vlc.EventType.MediaPlayerOpening, self.eOpening)
        events.event_attach(vlc.EventType.MediaPlayerBuffering, self.eBuffering)

        self._player.play()

        self._player.play()
        print ("NEXT")
        #self._player.set_pause(1)
        #self._player.next_frame()
        #self._player.set_time(30000)
        #time.sleep(1)
        #self._player.pause()
        #while self._player.get_state() == 4 or self._player.get_state() == 0:
        #    print(self._player.get_state())
        print(self._player.get_state())
        print("XX", self._player.get_state())
        
    def play(self):
        self._playing = True
        self._player.play()

    def stop(self):
        self._playing = False
        self._player.stop()
    def pause(self):
        if self._player.is_playing():
            self._playing = False
            self._player.pause()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    hd =  HyperDeckPlayer()
    _files = None
    _active_clip = None
    def parseArg(self, arg):
        return re.findall('([a-zA-Z][^:]+): ([^ ]+)', arg)

    def ActiveClip(self):
        if self._active_clip:
            return str(self._active_clip)
        else:
            return 'none'

    def buildSlotInfo(self, slot_id):
        if slot_id:
            out = ""
            out += "slot id: " + str(slot_id) + "\r\n"
            out += "status: mounted\r\n"
            out += "volume name: test\r\n"
            out += "recording time: 0\r\n"
            out += "video format: 1080p30\r\n"
            return out
        return None
    def buildRemote(self):
        out = ""
        out += "enabled: true\r\n"
        out += "override: false\r\n"
        return out

    def buildTransportInfo(self):
        if self.hd.is_playing():
            state = 'play'
        else:
            state = 'stopped'
        rate = int(self.hd.get_rate())
        if rate == 0:
            rate = 1;
        speed = str(int(self.hd.get_rate() * 100))
        (h,m,s,f) = self.hd.time_to_timecode(self.hd.get_time(), self.hd.get_fps())
        tc = f'{h:02}:{m:02}:{s:02}:{f:02}'
        out = ""
        out += 'status: ' + state + '\r\n'
        out += "speed: " + speed + "\r\n"
        out += "slot id: 1\r\n"
        out += "display timecode: " + tc + "\r\n"
        out += "timecode: " + tc + "\r\n"
        out += "clip id: " + self.ActiveClip() + "\r\n"
        out += "video format: 1080p30\r\n"
        out += "loop: false\r\n"
        return out
    def ffprobeFind(self, data, field):
        for item in data['streams']:
            if field in item:
                return item[field]
    def findVideoMetada(self, pathToInputVideo):
        cmd = "ffprobe -v quiet -print_format json -show_streams"
        args = shlex.split(cmd)
        args.append(pathToInputVideo)
        # run the ffprobe process, decode stdout into utf-8 & convert to JSON
        ffprobeOutput = subprocess.check_output(args).decode('utf-8')
        ffprobeOutput = json.loads(ffprobeOutput)
    
        # prints all the metadata available:
        #import pprint
        #pp = pprint.PrettyPrinter(indent=2)
        #pp.pprint(ffprobeOutput)
    
        # for example, find height and width
        print(ffprobeOutput)
        height = ffprobeOutput['streams'][0]['height']
        width = ffprobeOutput['streams'][0]['width']
        duration = self.ffprobeFind(ffprobeOutput, 'duration_ts')
        fps = ffprobeOutput['streams'][0]['avg_frame_rate']
        #print(width, height, duration, fps)
        return width, height, duration, fps

    def handle(self):
        out = "500 connection info:\r\n"
        out += "protocol version: 1.6\r\n"
        out += "model: Python Hyperdeck Server\r\n"
        out += "\r\n"
        response = bytes(out, 'ascii')
        self.request.sendall(response)

        while True:
            n = self.request.recv(1500)
            if n == b'':
                break
            print('Recv: ', n)
            data = str(n, 'ascii')
            self.process(data)
    def get_media(self, clip_id):
        return self._files[clip_id-1]

    def list_media(self):
        if self._files == None:
            self._files = os.listdir('videos')

        return self._files
    def process(self, data_recv):
        lines = data_recv.split('\n')
        data = lines[0]
        if 1==1:
            cur_thread = threading.current_thread()
            response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
            s = data.strip().split(":", 1)
            if s[0] == 'play':
                self.hd.play()
                if s[1]:
                    a = self.parseArg(s[1].strip())
                    for arg in a:
                        (param, val) = arg
                        if param == 'speed':
                            if val.strip() == '0':
                                self.hd.pause()
                            rate = int(val.strip())
                            self.hd.set_rate(rate/100)
                    pass
                else:
                    for line in lines:
                        s = line.strip().split(':', 1)
                        if s[0] == 'speed':
                            rate = int(s[1].strip())
                            self.hd.set_rate(rate/100)

                response = bytes("200 ok\r\n", 'ascii')
                #single clip: true
                #loop: false
                #speed: 100
            elif s[0] == 'stop':
                self.hd.pause()
                response = bytes("200 ok\r\n", 'ascii')

            elif s[0] == 'goto':
                s2 = s[1].strip().split(":", 1)
                if s2[0] == 'clip id':
                    if s2[1].strip()[:1] == '+':
                        self._active_clip += int(s2[1].strip()[1:])
                    elif s2[1].strip()[:1] == '-':
                        self._active_clip -= int(s2[1].strip()[1:])

                    else:
                        clipid = int(s2[1].strip())
                        self._active_clip = clipid
                    self.hd.load("videos/" + self.get_media(self._active_clip))
                    response = bytes("200 ok\r\n", 'ascii')
                else:
                    response = bytes("100 syntax error\r\n", 'ascii')
                goto: cl
            elif s[0] == 'slot info':
                s2 = s[1].strip().split(":", 1)
                if s2[0] == 'slot id':
                    out = "202 slot info:\r\n"
                    out += self.buildSlotInfo(s2[1].strip())
                    out += "\r\n"
                    response = bytes(out, 'ascii')
            elif s[0] == 'clips count':
                fl = self.list_media()
                out = "214 clips count:\r\n"
                out += "clip count: " + str(len(fl)) + "\r\n"
                out += "\r\n"
                response = bytes(out, 'ascii')
            elif s[0] == 'clips get':
                if len(s) == 1:
                    s2 = None
                else:
                    s2 = s[1].strip().split(":", 1)

                out = "205 clips info:\r\n"
                fl = self.list_media()
                at = 1
                if s2 and s2[0] == 'clip id':
                    clip_id = int(s2[1].strip())
                    fl = [fl[clip_id-1]]
                    at = clip_id
                else:
                    out += "clip count: " + str(len(fl)) + "\r\n"
                for f in fl:
                    print (f)
                    (width, height, duration, fps) = self.findVideoMetada('videos/' + f)
                    fps_s = fps.split('/')
                    fps_out = int(fps_s[0]) / int(fps_s[1])
                    (h,m,s,fr) = self.hd.time_to_timecode(duration, fps_out)
                    tc = f'{h:02}:{m:02}:{s:02}:{fr:02}'
                    #f = 'video' + str(at) + '.mp4'
                    out += str(at) + ":  " + f + " 00:00:00:00 " + tc + "\r\n" 
                    at += 1
                out += "\r\n"
                response = bytes(out, 'ascii')
            elif s[0] == 'notify':
                response = bytes("""200 ok\r\n""", 'ascii')
                bytes("""
transport: false
slot: false
remote: false
configuration: false


""", 'ascii')
            elif s[0] == 'remote':
                out = "210 remote info:\r\n"
                out += self.buildRemote()
                out += "\r\n"
                response = bytes(out, 'ascii')
            elif s[0] == 'transport info':
                """208 transport info:↵
	
status: {“preview”, “stopped”, “play”, “forward”, “rewind”,
“jog”, “shuttle”,”record”}↵
speed: {Play speed between -1600 and 1600 %}↵
slot id: {Slot ID or “none”}↵
display timecode: {timecode}↵
timecode: {timecode}↵
clip id: {Clip ID or “none”}↵
video format: {Video format}↵
loop: {“true”, “false”}↵
↵""" # https://youtu.be/4CxXM_YlAqc?t=416
                out = "208 transport info:\r\n"
                out += self.buildTransportInfo()
                out += "\r\n"
                response = bytes(out, 'ascii')
            else :
                response = bytes("200 ok\r\n", 'ascii')#100 syntax error\n", 'ascii')
            print('sent: ', response)
            self.request.sendall(response)
            """
            out = "508 transport info:\r\n"
            out += self.buildTransportInfo()
            out += "\r\n"
            response = bytes(out, 'ascii')
            self.request.sendall(response)

            out = "502 slot info:\r\n"
            out += self.buildSlotInfo(1)
            out += "\r\n"
            response = bytes(out, 'ascii')
            self.request.sendall(response)

            out = "510 remote info:\r\n"
            out += self.buildRemote()
            out += "\r\n"
            response = bytes(out, 'ascii')
            self.request.sendall(response)
            """
#        cur_thread = threading.current_thread()
#        response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
#        self.request.sendall(response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(bytes(message, 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "", 9993
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        server_thread.join()
#        server.shutdown()
