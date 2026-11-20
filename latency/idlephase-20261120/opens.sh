#!/bin/zsh
# opens.sh LABEL COUNT: COUNT opens of 8 impulses at 32 frames, as the wrapper's readiness probes; one line each.
label=$1; count=$2
app="/Users/bryandimaio/Development/USB-AoIP/tools/latency-harness/.build/USB16x16 Latency.app/Contents/MacOS/usb16x16-latency"
out="/Users/bryandimaio/Development/USB-AoIP/outputs/latency/idlephase-20261120/$label"; mkdir -p "$out"
for i in $(seq 1 $count); do
  f="$out/open-$(printf %03d $i).json"
  "$app" measure --device USB-AoIP --buffer-frames 32 --input-channel 1 --output-channel 1 --impulses 8 ${=OPENS_EXTRA:-} --maximum-lag-ms 200 --output "$f" >/dev/null 2>"$out/open-$(printf %03d $i).log"
  /usr/bin/python3 -c "
import json,sys
try:
    d=json.load(open(sys.argv[1])); p=d['correlation']['perImpulseDelaySamples']; print(sys.argv[2], d['capturedAt'], max(set(p),key=p.count), sorted(set(p)))
except Exception as e: print(sys.argv[2],'FAILED',e)" "$f" $i
  sleep 1
done
