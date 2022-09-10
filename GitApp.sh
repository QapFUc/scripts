#!/bin/bash
echo "I install program number 1"
mkdir GITApps
cd GITApps
git clone https://aur.archlinux.org/gdm-prime.git
cd gdm-prime
makepkg -sri
cd
echo "Success"
echo "I install program number 2"
cd GITApps
git clone https://aur.archlinux.org/gnome-browser-connector.git 
cd gnome-browser-connector
makepkg -sri
cd
echo "Success"
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
echo "I install program number 6"
cd GITApps
git clone https://aur.archlinux.org/touchegg.git
makepkg -sri
cd
echo "Success"
echo "I install program number 7"
cd GITApps
git clone https://aur.archlinux.org/appeditor-git.git
cd appeditor-git
makepkg -sri
cd
echo "Success"
echo "I install program number 8"
cd GITApps
git clone https://aur.archlinux.org/enpass-bin.git
cd enpass-bin
makepkg -sri
cd
"Success"
