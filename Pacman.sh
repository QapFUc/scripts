#!/bin/bash
echo "I install system program"
sudo pacman -S base-devel git pipewire pipewire-pulse pipewire-jack pipewire-media-session xorg xorg-xinit xorg-xrandr mesa-demos nvidia
echo "Success"
echo "I install WM"
sudo pacman -S gnome
echo "Success"
echo "I activated system program"
sudo pacman -S networkmanager
sudo systemctl enable NetworkManager
sudo systemctl start NetworkManager
echo "Success"
echo "I install favorite program"
sudo pacman -S audacity blender discord firefox htop inkscape kdenlive krita neofetch obs-studio qbittorrent scrcpy steam
echo "Success"
echo "I install git program"
chmod +x ~/scripts/GITApp.sh
./GITApp.sh
echo "Success"
