#!/bin/zsh
# cand48.sh LABEL [extra owner options]: the 48 kHz form of cand.sh (2026-11-22, item 5): stop the
# service, start the candidate with the running service's 48 kHz arguments (less --idle-phase, the
# rate-request file and the ppm file) and the preset the 48 kHz arms used, wait, 60 loaded opens.
# The service is NOT restarted here.
S=${0:A:h}; label=$1; shift
ARGS="--log-every 60 --rate 48000 --rx-queue 96 --prime-drop 28 --capture-drain --meter-file /dev/shm/cand-meters.txt --dsp-preset /etc/usb16x16/dsp/dante-immersive-one-sub.dsp --monitor-status /dev/shm/cand-monitor.status $*"
P() { ssh -o HostKeyAlias=audio-dev.local -o BatchMode=yes bdimaio@169.254.92.97 "$@"; }
P "sudo -n systemctl stop usb16x16-dante; sleep 2; sudo -n /usr/local/sbin/usb16x16-dante-candidate start /home/bdimaio/usb-16x16-work/dante-mode/owner/usb16x16-dante-owner-idlephase $ARGS" | tail -1
log=$(P 'ls -t /dev/shm/dante-owner-*.log | head -1'); echo "log $log"
P "grep -m1 -o 'rate=.*' $log"
until P "grep -q '^USB t=6' $log"; do sleep 5; done
OPENS_EXTRA="--other-channel-load-amplitude 0.1" "$S/opens.sh" $label ${OPENS:-60} > "$S/opens-$label.txt" 2>&1
echo "levels:"; awk '{print $3}' "$S/opens-$label.txt" | sort | uniq -c
echo "found:"; P "grep 'USBLINK.*tx=flow' $log | grep -o 'tx_prime_found=[0-9]*' | sort | uniq -c | tr '\n' ' '; echo; grep -c 'USBLINK.*tx=flow' $log; grep '^DSP t=' $log | tail -1 | cut -c1-60; grep '^USB t=' $log | tail -1 | grep -o 'capture_faults.*detaches=[0-9]*'"
P "cat $log" > "$S/owner-$label.txt"
