#!/bin/bash
echo "Open multilib in /etc/pacman.conf and change the server to the desired date"
read m
sudo pacman -S archlinux-keyring
sudo pacman -Syu
sudo pacman -S reflector rsync curl
sudo reflector --verbose --country 'Germany' -l 25 --sort rate --save /etc/pacman.d/mirrorlist
sudo pacman -R gnome-boxes cheese epiphany gnome-weather
sudo pacman -Syyuu
sudo pacman -S amd-ucode
sudo pacman -S intel-ucode
sudo pacman -S android-udev cmake gcc
sudo pacman -S nvidia
sudo pacman -S pipewire pipewire-pulse pipewire-jack gnome-bluetooth gnome-tweaks 
sudo pacman -S wine wine-mono wine-gecko
sudo pacman -S rclone fish neofetch scrcpy htop
sudo chsh -s /usr/bin/fish
chsh -s /usr/bin/fish
sudo systemctl enable bluetooth.service 
sudo pacman -S qbittorrent
sudo pacman -S vlc audacity
sudo pacman -S telegram-desktop thunderbird discord
sudo pacman -S blender inkscape kdenlive krita gimp obs-studio
sudo pacman -S noto-fonts-emoji noto-fonts ttf-liberation
sudo pacman -S steam

echo "You wish install Apps from aur? If no press Ctrl + C"
read m
mkdir ~/GITApps
cd GITApps
git clone https://aur.archlinux.org/gdm-prime.git
cd gdm-prime
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/optimus-manager.git 
cd optimus-manager
makepkg -sri
sudo echo "WaylandEnable=false" >> /etc/gdm/custom.conf
cd
cd GITApps
git clone https://aur.archlinux.org/gnome-browser-connector.git 
cd gnome-browser-connector
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/touchegg.git
cd touchegg
makepkg -sri
sudo systemctl enable touchegg.service
sudo systemctl start touchegg
cd
cd GITApps
git clone https://aur.archlinux.org/appeditor-git.git
cd appeditor-git
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/stacer.git
cd stacer
makepkg -sri
cd
cd GITApps
gpg --recv-keys 5E3C45D7B312C643
git clone https://aur.archlinux.org/spotify.git
cd spotify
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/enpass-bin.git
cd enpass-bin
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/timeshift.git 
cd timeshift
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/zoom.git
cd zoom
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/teams.git
cd teams
makepkg -sri
cd
cd GITApps
git clone https://aur.archlinux.org/onlyoffice-bin.git
cd onlyoffice-bin
makepkg -sri
cd
