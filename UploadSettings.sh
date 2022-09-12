#!/bin/bash
sudo chsh -s /usr/bin/fish
sudo pacman -S archlinux-keyring
sudo pacman -Syu
sudo pacman -S noto-fonts-emoji noto-fonts ttf-liberation
sudo pacman -S reflector rsync curl
sudo reflector --verbose --country 'Germany' -l 25 --sort rate --save /etc/pacman.d/mirrorlist
sudo pacman -Suy 
