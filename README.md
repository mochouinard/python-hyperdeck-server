# Python HyperDeck Server

This is a prototyping repo at this moment.  It actually work BUT the code was written quickly by try and errors without much clean up afterward and missing lot of error checking.

I do my dev on Ubuntu 20.04 and also test it on a Raspberry Pi 4 2GB (And a Raspberry Pi Zero W)

To install on a Raspberry Pi :
Using the Raspberry Pi Install tool, select Raspberry Pi OS Lite (32-bit) [Not the Desktop version]
```console
sudo apt update
sudo apt install -y git vlc python3-git ffmpeg python3-websockets python3-aiohttp python3-vlc python3-pyudev python3-psutil
git clone https://github.com/mochouinard/python-hyperdeck-server.git

sudo cp python-hyperdeck-server/systemd/hyperdeckemulator.service /lib/systemd/system/hyperdeckemulator.service

sudo systemctl daemon-reload
sudo systemctl enable "hyperdeckemulator"
sudo systemctl start "hyperdeckemulator" 
```
Then connect to your raspberry pi via HTTP to port 8082

More detailed instruction and maybe a package image will be comming in the next few weeks.  It will provide Info to configure Wifi and Static IP and a blackscreen when nothing is playing.
