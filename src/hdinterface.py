from hdplayer import HyperDeckPlayer

import os
import shlex
import subprocess
import json

class HyperDeckInterface:
    hd =  HyperDeckPlayer()
    _files = None
    _active_clip = None

    def ActiveClip(self):
        if self._active_clip:
            return str(self._active_clip)
        else:
            return 'none'

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
        return self._files[clip_id-1]

    def list_media(self):
        if self._files == None:
            self._files = os.listdir('videos')

        return self._files
    
    def load_clip(self, clip_id):
        vid = "videos/" + self.get_media(clip_id)
        if vid.endswith(".url"):
            with open(vid, 'r') as reader:
                vid = reader.readline().strip()
        print ("TTTTTTTTTTTTTTTTTTTTTTTTT", vid)
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
            return self.findVideoMetada("videos/" + self.get_media(clip_id))

    def findVideoMetada(self, pathToInputVideo):
        cmd = "ffprobe -v quiet -print_format json -show_streams"
        args = shlex.split(cmd)
        args.append(pathToInputVideo)
        # run the ffprobe process, decode stdout into utf-8 & convert to JSON
        try:
            ffprobeOutput = subprocess.check_output(args).decode('utf-8')
            ffprobeOutput = json.loads(ffprobeOutput)

            # prints all the metadata available:
            #import pprint
            #pp = pprint.PrettyPrinter(indent=2)
            #pp.pprint(ffprobeOutput)

            # for example, find height and width
            print(ffprobeOutput)
            height = self.ffprobeFind(ffprobeOutput, 'height')
            width = self.ffprobeFind(ffprobeOutput, 'width')
            duration = self.ffprobeFind(ffprobeOutput, 'duration_ts')
            fps = self.ffprobeFind(ffprobeOutput, 'avg_frame_rate')
            #print(width, height, duration, fps)
            return width, height, duration, fps
        except subprocess.CalledProcessError as e:
            print ("ffprobe error stdout output:\n", e.output)
            return None
