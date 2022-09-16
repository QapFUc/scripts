#!/bin/bash
cd
echo "I install system program"
sudo pacman -S base-devel git pipewire pipewire-pulse pipewire-jack xorg mesa-demos nvidia android-udev cmake gcc ligda
echo "Success"
read m
echo "I install WM"
sudo pacman -S gnome
echo "Success"
read m
echo "I activated system program"
sudo pacman -S networkmanager
sudo systemctl enable NetworkManager
sudo systemctl start NetworkManager
sudo pacman -Sy
echo "Success"
read m
echo "Open multilib in /etc/pacman.conf"
read m
sudo pacman -Sy
echo "I install favorite program"
sudo pacman -S rclone gnome-bluetooth gnome-tweaks telegram-desktop fish thunderbird vlc audacity blender discord firefox htop inkscape kdenlive krita gimp neofetch obs-studio qbittorrent scrcpy steam 
sudo systemctl enable bluetooth.service 
echo "Success"
