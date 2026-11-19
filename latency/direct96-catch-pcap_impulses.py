#!/usr/bin/env python3
"""pcap_impulses.py PI_IP RING...: every sample at 0.19..0.31 of full scale in the Dante flows
of a capture, per direction, flow and channel, as an absolute Dante sample stamp, and the
spacing between successive ones. Layout as tools/diag/dante-pcap-zeros.py."""
import struct, sys, collections
RATE = 96000
pi = sys.argv[1]
table = bytes(1 if (0x18 <= b <= 0x28 or 0xD8 <= b <= 0xE8) else 0 for b in range(256))
def packets(path):
    with open(path, "rb") as f:
        head = f.read(24)
        magic = struct.unpack("<I", head[:4])[0]
        nano = magic == 0xA1B23C4D
        while True:
            r = f.read(16)
            if len(r) < 16: return
            s, fr, cap, orig = struct.unpack("<IIII", r)
            d = f.read(cap)
            if len(d) < cap: return
            yield s + fr / (1e9 if nano else 1e6), d
state = {}; hits = collections.defaultdict(list); count = collections.Counter(); span = {}
order = collections.defaultdict(list)
for path in sys.argv[2:]:
    for when, fr in packets(path):
        if fr[12:14] != b"\x08\x00" or fr[23] != 17: continue
        ihl = (fr[14] & 15) * 4; u = 14 + ihl
        src = ".".join(map(str, fr[26:30])); dst = ".".join(map(str, fr[30:34]))
        sport, dport, ln = struct.unpack(">HHH", fr[u:u+6]); p = fr[u+8:u+ln]
        if len(p) < 12 or p[0] != 2: continue
        key = (src, sport, dst, dport)
        sec, smp = struct.unpack(">II", p[1:9]); audio = p[9:]; stamp = sec * RATE + smp
        st = state.get(key)
        if st is None:
            state[key] = {"last": stamp, "ch": None}; span[key] = [when, when, stamp, stamp]; continue
        if st["ch"] is None:
            step = stamp - st["last"]
            if step <= 0 or step > 512: st["last"] = stamp; continue
            st["ch"] = len(audio) // 3 // step; st["frames"] = step
        ch = st["ch"]; count[key] += 1
        if stamp < st["last"]: order[key].append((when, st["last"], stamp))
        elif stamp - st["last"] not in (st["frames"], 0): order[key].append((when, st["last"], stamp))
        st["last"] = stamp; span[key][1] = when; span[key][3] = stamp
        tops = audio[0::3]
        if b"\x01" not in tops.translate(table): continue
        for i, b in enumerate(tops):
            if table[b]:
                hits[(key, i % ch)].append((stamp + i // ch, when))
for key, st in state.items():
    d = "Pi sends" if key[0] == pi else "Pi receives"
    print(f"{d} {key[0]}:{key[1]} -> {key[2]}:{key[3]}: {st['ch']} channels, {st.get('frames')} frames a packet, {count[key]} packets, {span[key][1]-span[key][0]:.1f} s, stamp steps off the packet size: {len(order[key])}")
    for o in order[key][:6]: print("    odd step at", f"{o[0]:.6f}", o[2] - o[1])
for (key, c), h in sorted(hits.items(), key=lambda kv: (kv[0][0][0] != pi, kv[0][0], kv[0][1])):
    d = "Pi sends" if key[0] == pi else "Pi receives"
    stamps = [s for s, _ in h]
    sp = collections.Counter(b - a for a, b in zip(stamps, stamps[1:]))
    print(f"{d} flow :{key[1]}->:{key[3]} ch{c+1}: {len(h)} impulses, spacing {dict(sp)}")
    for (a, wa), (b, wb) in zip(h, h[1:]):
        if b - a != 24000: print(f"    {wb:.6f} stamp {b} is {b - a} after the one before (mod 24000: {b % 24000})")
    print("    stamps mod 24000:", dict(collections.Counter(s % 24000 for s in stamps)))
