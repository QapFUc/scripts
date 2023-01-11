#!/bin/bash
echo "Open multilib in /etc/pacman.conf and change the server to the desired date"
read yes
sudo pacman -Syu
sudo pacman -S archlinux-keyring
sudo pacman -Syu
sudo pacman -S reflector rsync curl
sudo reflector --verbose --country 'Germany' -l 25 --sort rate --save /etc/pacman.d/mirrorlist
sudo pacman -Syyuu
sudo pacman -S atril
sudo pacman -S cups
sudo systemctl enable cups.service
sudo systemctl start cups.service
cd driver/mccgdi-2.0.10-x86_64/
sudo ./install-driver
sudo pacman -S system-config-printer
cd ../
cd ./panamfs-scan-1.3.1-x86_64/
sudo ./install-driver
cd ../
cd ../
sudo pacman -S amd-ucode
sudo pacman -S intel-ucode
sudo pacman -S android-udev cmake gcc arduino jre17-openjdk xclip
sudo pacman -S nvidia-dkms
sudo pacman -S texlive-most textlive-lang
sudo pacman -S pipewire pipewire-pulse pipewire-jack 
sudo pacman -S wine wine-mono wine-gecko
sudo pacman -S rclone neofetch scrcpy btop neovim ranger fish
chsh -s /usr/bin/fish
sudo chsh -s /usr/bin/fish
sudo pacman -S qbittorrent bitwarden firefox
sudo pacman -S vlc audacity ranger
sudo pacman -S telegram-desktop thunderbird discord
sudo pacman -S blender inkscape kdenlive krita gimp obs-studio
sudo pacman -S noto-fonts-emoji noto-fonts ttf-liberation
sudo pacman -S steam

echo "You wish install Apps from aur? If no press Ctrl + C"
read yes
cd
mkdir ~/GITApps
cd GITApps
git clone https://aur.archlinux.org/stacer.git
cd stacer
makepkg -sric
cd
cd GITApps
git clone https://aur.archlinux.org/timeshift.git 
cd timeshift
makepkg -sric
cd
cd GITApps
git clone https://aur.archlinux.org/zoom.git
cd zoom
makepkg -sric
cd
cd GITApps
git clone https://aur.archlinux.org/teams.git
cd teams
makepkg -sric
cd
cd GITApps
git clone https://aur.archlinux.org/onlyoffice-bin.git
cd onlyoffice-bin
makepkg -sric
cd
cd GITApps
git clone https://aur.archlinux.org/clion.git
cd clion
makepkg -sric
cd
cd GITApps
git clone https://aur.archlinux.org/yandex-music-player.git
cd yandex-music-player
makepkg -sric
cd
