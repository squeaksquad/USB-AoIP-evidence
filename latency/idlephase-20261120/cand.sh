#!/bin/zsh
# cand.sh LABEL [extra owner options]: restart the candidate with the service's 96 kHz settings plus the options, wait, 60 loaded opens.
S=${0:A:h}; label=$1; shift
ARGS="--log-every 60 --rate 96000 --rx-queue 192 --rx-slack 192 --buffer 2048 --tx-lead 256 --guard 512 --usb-period 96 --usb-buffer 960 --prime-drop 96 --capture-drain --meter-file /dev/shm/cand-meters.txt --dsp-preset /etc/usb16x16/dsp/dante-immersive-one-sub@96000.dsp --monitor-status /dev/shm/cand-monitor.status $*"
P() { ssh -o HostKeyAlias=audio-dev.local -o BatchMode=yes bdimaio@169.254.92.97 "$@"; }
P "sudo -n /usr/local/sbin/usb16x16-dante-candidate stop; sleep 2; sudo -n /usr/local/sbin/usb16x16-dante-candidate start /home/bdimaio/usb-16x16-work/dante-mode/owner/usb16x16-dante-owner-idlephase $ARGS" | tail -1
log=$(P 'ls -t /dev/shm/dante-owner-*.log | head -1'); echo "log $log"
P "grep -m1 -o 'idle_phase_us=.*' $log"
until P "grep -q '^USB t=6' $log"; do sleep 5; done
OPENS_EXTRA="--other-channel-load-amplitude 0.1" "$S/opens.sh" $label ${OPENS:-60} > "$S/opens-$label.txt" 2>&1
echo "levels:"; awk '{print $3}' "$S/opens-$label.txt" | sort | uniq -c
echo "found:"; P "grep 'USBLINK.*tx=flow' $log | grep -o 'tx_prime_found=[0-9]*' | sort | uniq -c | tr '\n' ' '; echo; grep -c 'USBLINK.*tx=flow' $log; grep '^DSP t=' $log | tail -1 | cut -c1-60; grep '^USB t=' $log | tail -1 | grep -o 'capture_faults.*detaches=[0-9]*'"
P "cat $log" > "$S/owner-$label.log"
