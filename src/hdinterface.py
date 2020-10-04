from hdplayer import HyperDeckPlayer

import os
import shlex
import subprocess
import json
import pyudev
import psutil

import hashlib

from asyncio_event import asyncio_event

class HyperDeckInterface:
    hd =  HyperDeckPlayer()
    _files = None
    _active_clip = None
    _event = asyncio_event()
    _external_devices = []

    _ffprobe_cache = {}

    def ActiveClip(self):
        if self._active_clip:
            return str(self._active_clip)
        else:
            return 'none'
    async def refreshMedia(self):
        await self._event.emit("newmedia", None)

    def registerEvent(self, name, func):
        self._event.register(name, func)

    def buildSlotInfo(self, slot_id):
        if slot_id:
            out = [
                "slot id: " + str(slot_id),
                "status: mounted",
                "volume name: test",
                "recording time: 0",
                "video format: 1080p30"
                ]
            return out
        return None

    def get_media(self, clip_id):
        return self._files[clip_id-1]['location'] + '/' + self._files[clip_id-1]['filename']
    def get_disk_list(self):
        return self._external_devices;
    def list_media(self):
        #if self._files == None:
        self._files = []
        self._external_devices = []
        at = 1
        for f in os.listdir('videos'):
            details = self.loadVideoMetadata('videos' + '/' + f)
            (x, y, duration, fps) = self.findVideoMetadata('videos' + '/' + f)
            print('ttttttttttttttttttttttttttttttttt', duration)
            duration_str = '00:00:00'
            if duration <= 8000:
                duration_str = None
            thumb = self.thumbGen('videos' + '/' + f, duration_str)

            self._files.append({'clip_id': at, 'filename': f, 'location': 'videos', 'details': details, 'thumb': thumb})
            at += 1

        for p in psutil.disk_partitions():
            if p.mountpoint == '/':
                disk = psutil.disk_usage(p.mountpoint)
                self._external_devices.append({'location': p.mountpoint, 'device': p.device, 'opts': p.opts, 'usage': {'total': disk.total, 'used': disk.used, 'free': disk.free, 'percent': disk.percent}})

        context = pyudev.Context()

        removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if device.attributes.asstring('removable') == "1"]
        for device in removable:
            partitions = [device.device_node for device in context.list_devices(subsystem='block', DEVTYPE='partition', parent=device)]
            print("All removable partitions: {}".format(", ".join(partitions)))
            print("Mounted removable partitions:")
            for p in psutil.disk_partitions():
                if p.device in partitions:
                    disk = psutil.disk_usage(p.mountpoint)
                    self._external_devices.append({'location': p.mountpoint, 'device': p.device, 'opts': p.opts, 'usage': {'total': disk.total, 'used': disk.used, 'free': disk.free, 'percent': disk.percent}})
                if p.device in partitions:
                    print("  {}: {}".format(p.device, p.mountpoint))
                    for f in os.listdir(p.mountpoint):
                        details = self.loadVideoMetadata(p.mountpoint + '/' + f)
                        thumb = self.thumbGen(p.mountpoint + '/' + f)

                        self._files.append({'clip_id': at, 'filename': f, 'location': p.mountpoint, 'device': p.device, 'details': details, 'thumb': thumb})
                        at += 1

        print (self._external_devices)
        return self._files
    
    def load_clip(self, clip_id):
        vid = self.get_media(clip_id)
        if vid.endswith(".url"):
            with open(vid, 'r') as reader:
                vid = reader.readline().strip()
        self.hd.load(vid)
        self._active_clip = clip_id

    def buildRemote(self):
        out = [
                "enabled: true",
                "override: false"
                ]
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
        out = [
                'status: ' + state,
                "speed: " + speed,
                "slot id: 1",
                "display timecode: " + tc,
                "timecode: " + tc,
                "clip id: " + self.ActiveClip(),
                "video format: 1080p30",
                "loop: false"
                ]
        return out
    def ffprobeFind(self, data, field):
        for item in data['streams']:
            if field in item:
                return item[field]

    def findClipMetadata(self, clip_id):
            return self.findVideoMetadata(self.get_media(clip_id))

    def thumbGen(self, pathToInputVideo, pos):
        
        m = hashlib.md5()
        m.update(pathToInputVideo.encode('utf-8'))
        fname = m.hexdigest()
        if os.path.exists('thumbs/' + fname + '.png'):
            return fname
        url = pathToInputVideo
        if url.endswith('.url'):
            with open(url, 'r') as f:
                url = f.readline().strip()
        args = shlex.split('ffmpeg')
        if pos:
            args += shlex.split('-ss')
            args.append(pos)
        args += shlex.split('-i')
        args.append(url)
        args += shlex.split('-vframes 1 -filter:v scale="280:-1" -y')
        args.append('thumbs/' + fname + '.png')
        print(' '.join(args))
        try:
            ffprobeOutput = subprocess.check_output(args).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print ("ffmpeg error stdout output:\n", e.output)
            return None
        return fname

    def loadVideoMetadata(self, pathToInputVideo):
        ffprobeOutput = None

        if pathToInputVideo in self._ffprobe_cache:
            ffprobeOutput = self._ffprobe_cache[pathToInputVideo]['json']
        else:
            url = pathToInputVideo
            if url.endswith('.url'):
                with open(url, 'r') as f:
                    url = f.readline().strip()
            cmd = "ffprobe -v quiet -print_format json -show_streams"
            args = shlex.split(cmd)
            args.append(url)
            # run the ffprobe process, decode stdout into utf-8 & convert to JSON
            try:
                ffprobeOutput = subprocess.check_output(args).decode('utf-8')
                ffprobeOutput = json.loads(ffprobeOutput)
                self._ffprobe_cache[pathToInputVideo] = {'json':ffprobeOutput}
            except subprocess.CalledProcessError as e:
                print ("ffprobe error stdout output:\n", e.output)
                return None

        # prints all the metadata available:
        #import pprint
        #pp = pprint.PrettyPrinter(indent=2)
        #pp.pprint(ffprobeOutput)
        return ffprobeOutput
    def findVideoMetadata(self, pathToInputVideo):
        ffprobeOutput = self.loadVideoMetadata(pathToInputVideo)
        # for example, find height and width
        print(ffprobeOutput)
        height = self.ffprobeFind(ffprobeOutput, 'height')
        width = self.ffprobeFind(ffprobeOutput, 'width')
        duration = self.ffprobeFind(ffprobeOutput, 'duration_ts')
        fps = self.ffprobeFind(ffprobeOutput, 'avg_frame_rate')
        #print(width, height, duration, fps)
        return width, height, duration, fps
