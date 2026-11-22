#!/usr/bin/env python3
"""pcap_offsets.py PI_IP RING...: for a capture of both directions of the Dante flows taken
during a bit-exact run, find which channel the far loop returns each outgoing channel on and
at what stamp offset (return stamp minus outgoing stamp of the same sample), then follow that
offset sample by sample and report every place it changes. A constant offset on every channel
means the wire carries back exactly what the Pi sent, in place; a step means the far loop
moved the stream. Layout as tools/diag/dante-pcap-zeros.py. Stdlib only."""
import collections, struct, sys

RATE = 96000
pi = sys.argv[1]


def packets(path):
    with open(path, "rb") as f:
        head = f.read(24)
        nano = struct.unpack("<I", head[:4])[0] == 0xA1B23C4D
        while True:
            r = f.read(16)
            if len(r) < 16:
                return
            s, fr, cap, _ = struct.unpack("<IIII", r)
            d = f.read(cap)
            if len(d) < cap:
                return
            yield s + fr / (1e9 if nano else 1e6), d


flows = collections.defaultdict(dict)  # key -> stamp -> (when, audio)
for path in sys.argv[2:]:
    for when, fr in packets(path):
        if fr[12:14] != b"\x08\x00" or fr[23] != 17:
            continue
        u = 14 + (fr[14] & 15) * 4
        src = ".".join(map(str, fr[26:30])); dst = ".".join(map(str, fr[30:34]))
        sport, dport, ln = struct.unpack(">HHH", fr[u:u + 6]); p = fr[u + 8:u + ln]
        if len(p) < 12 or p[0] != 2:
            continue
        sec, smp = struct.unpack(">II", p[1:9])
        flows[(src, sport, dst, dport)][sec * RATE + smp] = (when, p[9:])

chans = {}  # (key, c) -> (stamp0, [samples], when0)
for key, pk in flows.items():
    stamps = sorted(pk)
    steps = collections.Counter(b - a for a, b in zip(stamps, stamps[1:]))
    frames = steps.most_common(1)[0][0]
    ch = len(pk[stamps[0]][1]) // 3 // frames
    gaps = sum(n for s, n in steps.items() if s != frames)
    d = "Pi sends" if key[0] == pi else "Pi receives"
    print(f"{d} :{key[1]} -> :{key[3]}: {ch} ch, {frames} frames, {len(stamps)} packets, "
          f"{pk[stamps[-1]][0] - pk[stamps[0]][0]:.1f} s, stamp steps off the packet size: {gaps}")
    s0 = stamps[0]; n = stamps[-1] + frames - s0
    raw = bytearray(n * ch * 3)
    for s in stamps:
        a = pk[s][1]; o = (s - s0) * ch * 3
        raw[o:o + len(a)] = a
    st = ch * 3
    for c in range(ch):
        vals = [(x << 16) | (y << 8) | z for x, y, z in zip(raw[3 * c::st], raw[3 * c + 1::st], raw[3 * c + 2::st])]
        chans[(key, c)] = (s0, vals, pk[s0][0])

out = {k: v for k, v in chans.items() if k[0][0] == pi}
ret = {k: v for k, v in chans.items() if k[0][0] != pi}


def name(k):
    return f":{k[0][1]}->:{k[0][3]} ch{k[1] + 1}"


SEARCH = 4096
pairs = []
for rk, (r0, rv, _) in sorted(ret.items(), key=lambda kv: (kv[0][0][3], kv[0][1])):
    i = len(rv) // 2
    while i < len(rv) - 64 and (rv[i] == 0 or len(set(rv[i:i + 32])) < 24):
        i += 97
    if i >= len(rv) - 64:
        print(f"return {name(rk)}: no signal")
        continue
    win = rv[i:i + 32]; found = None
    for ok, (o0, ov, _) in out.items():
        t = r0 + i  # stamp of win[0] on return
        for dd in range(0, SEARCH):
            j = t - dd - o0
            if 0 <= j and j + 32 <= len(ov) and ov[j] == win[0] and ov[j:j + 32] == win:
                found = (ok, dd); break
        if found:
            break
    if not found:
        print(f"return {name(rk)}: carries no outgoing channel within {SEARCH} stamps")
        continue
    pairs.append((rk, found[0], found[1]))
    print(f"return {name(rk)} = outgoing {name(found[0])} at stamp offset {found[1]}")

print()
for rk, ok, d0 in pairs:
    r0, rv, rw = ret[rk]; o0, ov, _ = out[ok]
    d = d0; events = []; bad = 0; held = collections.Counter()
    t = r0
    end = r0 + len(rv)
    while t < end:
        j = t - d - o0
        if 0 <= j < len(ov) and rv[t - r0] == ov[j]:
            held[d] += 1; t += 1; continue
        if not (0 <= j < len(ov)):
            t += 1; continue
        w = rv[t - r0:t - r0 + 6]
        nd = None
        for k in sorted(range(-64, 65), key=abs):
            jj = t - (d + k) - o0
            if k and 0 <= jj and jj + 6 <= len(ov) and ov[jj:jj + 6] == w:
                nd = d + k; break
        if nd is None:
            bad += 1; t += 1; continue
        events.append((t, d, nd)); d = nd
    print(f"{name(rk)} <- {name(ok)}: samples by offset {dict(held)}, unmatched {bad}, offset changes {len(events)}")
    for t, a, b in events[:40]:
        print(f"    {rw + (t - r0) / RATE:.6f} stamp {t}: {a} -> {b} ({b - a:+d})")
