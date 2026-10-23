"""Writes irregular.sgy: a synthetic SEG-Y whose live traces have a known exact convex hull.

Lattice (i, j), i in 0..8, j in 0..12, with two corners cut (i + j < 2, (8-i) + (12-j) < 3),
rotated by the 3-4-5 angle and placed in ED50 / UTM 31N at (605000, 6080000), 25 m spacing:
  x = 605000 + 20 i - 15 j,  y = 6080000 + 15 i + 20 j   (metres; stored in cm, scalar -100)
Hull vertices by construction, lattice (2,0) (8,0) (8,9) (5,12) (0,12) (0,2). One dead trace
(trace identification code 2) at (0, 0) must not count. Traces are written in a shuffled order.
Run: python make_segy.py   (from this directory)
"""
import random
import struct

traces = [(i, j) for i in range(9) for j in range(13) if i + j >= 2 and (8 - i) + (12 - j) >= 3]
random.Random(3).shuffle(traces)
samples = 4
head = bytearray(b"C01 SYNTHETIC IRREGULAR SURVEY FOR OSD E03 HULL TEST".ljust(3200))
binary = bytearray(400)
struct.pack_into(">H", binary, 3220 - 3200, samples)   # samples per trace
struct.pack_into(">H", binary, 3224 - 3200, 5)         # IEEE float
struct.pack_into(">H", binary, 3254 - 3200, 1)         # measurement system: metres
out = head + binary


def trace(x_cm, y_cm, code=1):
    h = bytearray(240)
    struct.pack_into(">h", h, 28, code)
    struct.pack_into(">h", h, 70, -100)
    struct.pack_into(">i", h, 180, x_cm)
    struct.pack_into(">i", h, 184, y_cm)
    return h + struct.pack(">4f", 0, 0, 0, 0)


out += trace(0, 0, code=2)
for i, j in traces:
    out += trace((605000 + 20 * i - 15 * j) * 100, (6080000 + 15 * i + 20 * j) * 100)
with open("irregular.sgy", "wb") as f:
    f.write(out)
