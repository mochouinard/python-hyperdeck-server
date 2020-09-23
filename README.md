# Python HyperDeck Server

This is a prototyping repo at this moment.

2020-09-22 : This was tested ONLY with the BM Hyperdeck Python SDK Client you can download at : https://downloads.blackmagicdesign.com/Developer/HyperDeck/20191021-c99749/Blackmagic_HyperDeck_Developer_SDK_1.0.zip

To use this software, you put your video file in the videos folders (basic ascii with no space in file name... I haven't done any escaping at all yet), then just start python3 src/prototype_server.py 

You can now connect to your computer IP address to port 9993 which is the standard hyperdeck port

Required packages :
Python3
python-vlc
