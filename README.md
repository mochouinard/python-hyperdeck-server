# Python HyperDeck Server

This is a prototyping repo at this moment.  It actually work BUT the code was written quickly by try and errors without much clean up afterward and missing lot of error checking.

I do my dev on Ubuntu 20.04 and also test it on a Raspberry Pi 4 2GB (And a Raspberry Pi Zero W)

To install on a Raspberry Pi :
Using the Raspberry Pi Install tool, select Raspberry Pi OS Lite (32-bit) [Not the Desktop version]

Login to your raspberry pi with user pi and run the following command (Require internet access)
```console
sudo apt update
sudo apt install -y git vlc python3-git ffmpeg python3-websockets python3-aiohttp python3-vlc python3-pyudev python3-psutil
git clone https://github.com/mochouinard/python-hyperdeck-server.git

sudo cp python-hyperdeck-server/systemd/hyperdeckemulator.service /lib/systemd/system/hyperdeckemulator.service

sudo systemctl daemon-reload
sudo systemctl enable "hyperdeckemulator"
sudo systemctl start "hyperdeckemulator" 
```
Then connect to the web UI, go to http://[Raspberry Pi IP]:8082/

To find your IP, you can type : hostname -I

To configure the wifi interface, run raspi-config

More detailed instruction and maybe a package image will be comming in the next few weeks.  It will provide Info to configure Wifi and Static IP and a blackscreen when nothing is playing.

The following is if you want to setup the overlay which require X server an chromium.
```console
sudo apt-get install -y xserver-xorg x11-xserver-utils xinit openbox chromium-browser lightdm unclutter

cat << EOF | sudo tee -a /etc/xdg/openbox/autostart
xset s off
xset s noblank
xset -dpms

# Allow quitting the X server with CTRL-ATL-Backspace
setxkbmap -option terminate:ctrl_alt_bksp

@unclutter -idle 0

# Start Chromium in kiosk mode
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/'Local State'
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/; s/"exit_type":"[^"]\+"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences
chromium-browser --disable-component-update --disable-infobars --kiosk 'http://127.0.0.1:8082/kiosk/'
EOF

systemctl set-default graphical.target
ln -fs /lib/systemd/system/getty@.service /etc/systemd/system/getty.target.wants/getty@tty1.service
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF
sed /etc/lightdm/lightdm.conf -i -e "s/^\(#\|\)autologin-user=.*/autologin-user=$USER/"
```
