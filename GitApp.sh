#!/bin/bash
cd

echo "I install program number 3"
cd GITApps
git clone https://aur.archlinux.org/spotify.git
cd spotify
makepkg -sri
cd
echo "Success"
echo "I install program number 4"
cd GITApps
git clone https://aur.archlinux.org/stacer.git
cd stacer
makepkg -sri
cd
echo "Success"
echo "I install program number 5"
cd GITApps
git clone https://aur.archlinux.org/teams.git
cd teams
makepkg -sri
cd
echo "Success"
echo "I install program number 8"
cd GITApps
git clone https://aur.archlinux.org/enpass-bin.git
cd enpass-bin
makepkg -sri
cd
echo "Success"
echo "I install program number 9"
cd GITApps
git clone https://aur.archlinux.org/zoom.git
cd zoom
makepkg -sri
cd
echo "Success"
echo "I install program number 10"
cd GITApps
git clone https://aur.archlinux.org/optimus-manager.git 
cd optimus-manager
makepkg -sri
cd
sudo echo "WaylandEnable=false" >> /etc/gdm/custom.conf
echo "Success"
echo "I install program number 11"
cd GITApps
git clone https://aur.archlinux.org/timeshift.git 
cd timeshift
makepkg -sri
cd
echo "Success"
echo "I install program number 12"
cd GITApps
git clone https://aur.archlinux.org/onlyoffice-bin.git
cd onlyoffice-bin
makepkg -sri
cd
echo "Success"
