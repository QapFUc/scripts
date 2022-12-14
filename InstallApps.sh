#!/bin/bash
echo "Open multilib in /etc/pacman.conf and change the server to the desired date"
read m
sudo pacman -S archlinux-keyring
sudo pacman -Syu
sudo pacman -S reflector rsync curl
sudo reflector --verbose --country 'Germany' -l 25 --sort rate --save /etc/pacman.d/mirrorlist
sudo pacman -Syyuu
sudo pacman -S dbus-broker
sudo systemctl enable dbus-broker.service
sudo systemctl disable dbus.service
sudo pacman -S evince
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
sudo pacman -S android-udev cmake gcc arduino jre8-openjdk
sudo pacman -S nvidia
sudo pacman -S texlive-most textlive-lang
sudo pacman -S pipewire pipewire-pulse pipewire-jack gnome-bluetooth gnome-tweaks
sudo pacman -S gnome-shell gnome-console gnome-tweak-tool gnome-control-center gdm gnome-keyring nautilus file-roller gnome-text-editor gnome-calculator
sudo pacman -S dconf-editor login-manager-settings 
sudo pacman -S wine wine-mono wine-gecko
sudo pacman -S rclone fish neofetch scrcpy htop btop
sudo chsh -s /usr/bin/fish
chsh -s /usr/bin/fish
sudo systemctl enable bluetooth.service 
sudo pacman -S qbittorrent bitwarden
sudo pacman -S vlc audacity
sudo pacman -S telegram-desktop thunderbird discord
sudo pacman -S blender inkscape kdenlive krita gimp obs-studio
sudo pacman -S noto-fonts-emoji noto-fonts ttf-liberation
sudo pacman -S steam

echo "You wish install Apps from aur? If no press Ctrl + C"
read m
cd
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
echo "WaylandEnable=false" >> /etc/gdm/custom.conf
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
cd GITApps
git clone https://aur.archlinux.org/paru.git
cd paru
makepkg -sri
cd
paru -S protonvpn
cd GITApps
git clone https://aur.archlinux.org/clion.git
cd clion
makepkg -sri
cd




