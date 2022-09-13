#!/bin/bash
cd
echo "I install system program"
sudo pacman -S base-devel git pipewire pipewire-pulse pipewire-jack xorg mesa-demos nvidia android-udev andoid-tools cmake
echo "Success"
read m
echo "I install WM"
sudo pacman -S plasma
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
sudo pacman -S dolphin alacritty djvulibre rclone telegram-desktop fish thunderbird vlc audacity blender discord firefox htop inkscape kdenlive krita neofetch obs-studio qbittorrent scrcpy steam
echo "Success"
