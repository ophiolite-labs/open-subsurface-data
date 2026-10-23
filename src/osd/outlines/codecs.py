"""Blosc 1 frames with LZ4 blocks, the compressor of the MDIO stores we read (Zarr v2).

Pure Python so the outline extractor needs no compiled codec. Only what MDIO writes is
accepted: LZ4 or memcpyed blocks, optional byte shuffle, split or unsplit streams; anything
else is a ValueError naming what was found.
"""

from __future__ import annotations

import struct

MEMCPYED, DONT_SPLIT, SHUFFLE, BITSHUFFLE = 0x02, 0x10, 0x01, 0x04
LZ4 = 1


def lz4_block(src: bytes, size: int) -> bytes:
    out = bytearray()
    i, n = 0, len(src)
    while i < n:
        token = src[i]
        i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        out += src[i:i + lit]
        i += lit
        if i >= n:
            break
        offset = src[i] | (src[i + 1] << 8)
        i += 2
        length = token & 15
        if length == 15:
            while True:
                b = src[i]
                i += 1
                length += b
                if b != 255:
                    break
        length += 4
        if offset == 0 or offset > len(out):
            raise ValueError("lz4: offset outside the output")
        start = len(out) - offset
        if offset >= length:
            out += out[start:start + length]
        else:  # overlapping copy repeats the last `offset` bytes
            seg = bytes(out[start:])
            out += (seg * (length // offset + 1))[:length]
    if len(out) != size:
        raise ValueError(f"lz4: block decoded to {len(out)} bytes, expected {size}")
    return bytes(out)


def unshuffle(b: bytes, typesize: int) -> bytes:
    n = len(b) // typesize
    if typesize == 1 or n == 0:
        return b
    out = bytearray(len(b))
    for k in range(typesize):
        out[k:n * typesize:typesize] = b[k * n:(k + 1) * n]
    out[n * typesize:] = b[n * typesize:]
    return bytes(out)


def blosc_decode(buf: bytes) -> bytes:
    if len(buf) < 16:
        raise ValueError("blosc: frame shorter than its header")
    flags, typesize = buf[2], buf[3]
    nbytes, blocksize, _cbytes = struct.unpack_from("<III", buf, 4)
    if flags & MEMCPYED:
        return bytes(buf[16:16 + nbytes])
    if flags >> 5 != LZ4 or flags & BITSHUFFLE:
        raise ValueError(f"blosc: compressor {flags >> 5}, flags {flags:#x}; only lz4 with byte shuffle")
    nblocks = -(-nbytes // blocksize)
    starts = struct.unpack_from(f"<{nblocks}I", buf, 16)
    out = bytearray()
    for b, start in enumerate(starts):
        leftover = b == nblocks - 1 and nbytes % blocksize
        bsize = nbytes % blocksize if leftover else blocksize
        split = not flags & DONT_SPLIT and typesize <= 16 and blocksize // typesize >= 128 and not leftover
        streams = typesize if split else 1
        each = bsize // streams
        p, block = start, bytearray()
        for _ in range(streams):
            csize = struct.unpack_from("<I", buf, p)[0]
            p += 4
            block += buf[p:p + csize] if csize == each else lz4_block(buf[p:p + csize], each)
            p += csize
        out += unshuffle(bytes(block), typesize) if flags & SHUFFLE else block
    return bytes(out)
