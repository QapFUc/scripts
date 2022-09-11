#!/bin/bash
chmod +x GitApp.sh
chmod +x Pacman.sh
./Pacman.sh
./GitApp.sh
sudo 7z x applications.7z -o/usr/share/
sudo 7z x .config.7z -o/home/qapfuc/
sudo 7z x .local.7z -o/home/qapfuc
