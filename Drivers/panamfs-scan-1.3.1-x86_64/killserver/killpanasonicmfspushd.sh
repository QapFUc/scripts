#! /bin/sh

/usr/local/share/panasonic/scanner/bin/killpanasonicmfspushd
killall PanasonicMFSpushd
rm /var/tmp/com.panasonic.mfs.killserver.lock
exit 0
