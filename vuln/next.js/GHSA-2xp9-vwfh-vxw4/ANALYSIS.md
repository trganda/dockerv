# Vulnerability Analysis Report

## Unauthenticated RCE in Next.js Image Optimization API via malicious AVIF (GHSA-2xp9-vwfh-vxw4)

| Item | Detail |
|------|--------|
| Advisory | [GHSA-2xp9-vwfh-vxw4](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4) |
| Title | Unauthenticated Remote Code Execution in Image Optimization API when AVIF files are used |
| Package | `next` (npm) |
| Affected | `next >= 10.0.0 < 15.5.24`, `next < 16.3.3` |
| Patched | `15.5.24`, `16.3.3` |
| Severity | Critical — CVSS 4.0 `AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H` (9.5) |
| CVE | none assigned at time of writing |
| Underlying bug | [GHSA-g89c-p67h-r497](https://github.com/strukturag/libheif/security/advisories/GHSA-g89c-p67h-r497) — libheif heap buffer overflow, affected `<= 1.23.1`, patched `1.23.2` |
| Fix commit | `409772ec807def20132d251ad48fd8d8ad4c73c2` — `[15.5.x] [next/image]: disable avif image optimization` |

---

## 1. Summary

Next.js ships an image optimization API at `/_next/image`. For any
`image/avif` input it decodes the image with `sharp` (libvips → libheif) and
re-encodes it at the requested size. A crafted AVIF file exploiting
GHSA-g89c-p67h-r497 causes `HeifPixelImage::scale_nearest_neighbor()` in
libheif to write 16-bit samples into an 8-bit Alpha-plane allocation — a
heap buffer overflow whose size and written values are attacker controlled.
An unauthenticated attacker triggers it with a single `GET` to
`/_next/image?url=/poc.avif&w=...&q=...`. The advisory authors report having
achieved RCE on multiple applications using `heif_decode_image()`.

Next.js mitigated the issue by disabling AVIF optimization entirely until a
fixed libheif propagates into the `sharp` prebuilt binaries.

## 2. Root Cause (libheif ≤ 1.23.1)

The overflow is a chain of four individually benign behaviors in
`HeifPixelImage` / `ImageItem`:

1. **`transfer_channel_from_image_as()` accepts duplicate destination channels.**
   It moves a source plane into the destination image by re-labeling it as
   `dst_channel` and appending it to `m_storage` unconditionally — the code
   even contains `// TODO: check that dst_channel does not exist yet`.

2. **`find_storage_for_channel()` returns only the first match.**
   All dependent methods (`get_bits_per_pixel()`, `get_channel_memory()`,
   `get_width()`, `get_height()`) describe only the first Alpha plane, even
   when later duplicates have different bit depth and allocation size.

3. **`scale_nearest_neighbor()` underallocates, then overwrites via the HDR branch.**
   The destination Alpha plane is allocated with the bit depth of the first
   Alpha entry (`pixelimage.cc:1849`):

   ```cpp
   if (has_channel(heif_channel_Alpha)) {
       out_img->add_channel(heif_channel_Alpha, width, height,
                            get_bits_per_pixel(heif_channel_Alpha), limits); // first Alpha's depth
   }
   ```

   The scaling loop then iterates **every** entry in `m_storage`
   (`pixelimage.cc:1917-1965`). For each duplicate Alpha it looks up the same
   destination buffer, but selects the write type from **that component's**
   bit depth. A later 10-bit Alpha takes the HDR branch, casts the 8-bit
   destination to `uint16_t*` and writes 2 bytes per sample into a
   1-byte-per-sample allocation:

   ```cpp
   uint16_t* out_data = out_img->get_channel_memory<uint16_t>(channel, &out_stride);
   out_stride /= 2;
   ...
   out_data[y * out_stride + x] = in_data[iy * in_stride + ix];  // 2-byte write into 1-byte alloc
   ```

4. **`iden` enables the nested item graph that produces duplicate Alphas.**
   `ImageItem_iden::decode_compressed_image()` calls the referenced item's
   **full** `decode_image()` (which already attaches its own alpha), then the
   base-class `ImageItem::decode_image()` attaches the iden item's own alpha
   via `transfer_channel_from_image_as()` — producing two Alpha entries in
   `m_storage` (8-bit and 10-bit). Additionally
   `ImageItem_iden::check_decoded_image_size()` unconditionally returns
   `Error::Ok`, allowing the iden's declared `ispe` dimensions to differ from
   the referenced item's real dimensions — the mismatch that forces
   `scale_nearest_neighbor()`.

### 1.23.2 fix

The fix rejects duplicate channels in the transfer path and/or makes the
scaler use each plane's own storage instead of the first match.

## 3. Crafted File Layout (PoC)

Five ISOBMFF items:

| Item | Type | Size | Role |
|------|------|------|------|
| 1 | hvc1/av01 | 64×64 8-bit | color image, aux alpha → item 2 |
| 2 | hvc1/av01 | 64×64 8-bit | alpha aux of item 1 |
| 3 | iden | 64×64 (ispe) | derives from item 1; alpha aux of item 5; own alpha → item 4 |
| 4 | hvc1/av01 | 64×64 **10-bit** | alpha aux of item 3 |
| 5 | hvc1/av01 | 128×128 8-bit | **primary item**, alpha → item 3 |

Decoding the primary item (5) yields `m_storage = [Y, Cb, Cr, Alpha(8-bit),
Alpha(10-bit)]` on the iden-derived image, then `scale_nearest_neighbor()`
scales the 64×64 alpha to the 128×128 primary: allocates 128×128×1 = 16,384
bytes but writes 128×128×2 = 32,768 bytes — **~16 KB overflow**. The primary
size controls the overflow extent; the HEVC/AV1 sample values control the
written bytes. A 512×512 primary overflows ~256 KB.

## 4. Next.js Integration

`packages/next/src/server/image-optimizer.ts`:

- `detectContentType()` sniffs the ftyp major brand `avif` → `image/avif`.
- In vulnerable versions `BYPASS_TYPES = [SVG, ICO, ICNS, BMP, JXL, HEIC]` —
  AVIF is **not** bypassed.
- `imageOptimizer()` then calls `optimizeImage()`:

  ```ts
  const transformer = sharp(buffer, {...}).timeout({seconds: 7}).rotate()
  transformer.resize(width, ...)
  if (contentType === AVIF) transformer.avif({ quality: ..., effort: 3 })
  await transformer.toBuffer()   // <- libvips heifload -> heif_decode_image -> overflow
  ```

- libvips 8.18 `heifload.c` decodes exactly via
  `heif_decode_image(handle, ..., heif_colorspace_RGB, chroma-with-alpha, ...)`
  — the API called out by the libheif advisory as affected.
- If `optimizeImage()` throws, Next.js falls back to serving the original
  bytes, which is why a *failed* decode (e.g. unsupported codec) looks like a
  "bypass" even on vulnerable builds.

## 5. Trigger Conditions (how the attacker reaches the decoder)

The exploit requires the malicious AVIF to be reachable as the `url`
parameter of `/_next/image` — **no upload into the victim app is required**
and the trigger is a single unauthenticated GET. `imageParamsValidation()`
(`image-optimizer.ts`) accepts two kinds of URLs:

### A. Local path — `url=/...` (enabled by default)

- Default `images.localPatterns` is unset → `hasLocalMatch()` returns true,
  **any** local path is allowed.
- The bytes are served by the app itself (`fetchInternalImage()`
  re-dispatches the path through the app's own router), so the file must be
  reachable via:
  - `public/` static assets, or
  - any app route that serves user content (avatar/profile upload endpoints,
    UGC storage proxied by the app, etc.).
- A user-facing upload feature is the most common vector. The payload is only
  a few hundred bytes and `detectContentType()` only sniffs the ftyp `avif`
  brand bytes — it does not need to be a valid image.

### B. Remote URL — `url=https://...` (SSRF-style, opt-in)

- `url` must be absolute `http(s)` and match
  `hasRemoteMatch(images.domains, images.remotePatterns, url)`.
- Defaults `domains: []` / `remotePatterns: []` reject **all** remote URLs
  (`'"url" parameter is not allowed'`). Only apps that configured remote
  patterns (common when optimizing CMS/CDN/S3 images, often
  `hostname: '**'`) expose this path.
- When enabled it is a real SSRF surface; the only mitigations in
  `fetchExternalImage()` are:
  - DNS resolution + `isPrivateIp()` check — private IPs rejected unless
    `images.dangerouslyAllowLocalIP = true` (publicly routable attacker
    hosts work fine),
  - 7 s timeout, max 3 manual redirects, `maximumResponseBody` size cap.

Either way the attacker only needs a URL the server can fetch: their own
public payload URL (path B) or a way to have the file served by the app
(path A).

## 6. Dependency Version Analysis (why the exploit needs sharp ≥ 0.35.x)

| sharp | @img/sharp-libvips | libvips | libheif | overflow reachable? |
|-------|--------------------|---------|---------|---------------------|
| 0.34.3 | 1.2.0 | 8.17.1 | 1.20.1 | **no** — planes stored in `std::map<heif_channel, ImagePlane>`; duplicate Alpha planes collapse on insert |
| 0.35.0/1 | 1.3.0/1 | 8.18.3 | 1.23.0 | **yes** |
| 0.35.2/3 | 1.3.2 | 8.18.3 | 1.23.1 | **yes** |

The vulnerable `std::vector<ComponentStorage> m_storage` model (allowing
duplicate channels) was introduced in **libheif 1.22.0**. The advisory's
"affected ≤ 1.23.1" is conservative; the overflow is practically reachable
only on 1.22.0–1.23.1.

`next@16.3.2` declares `"sharp": "^0.35.3"` (optionalDependencies), so the
default install resolves sharp 0.35.3 → libheif 1.23.1 → vulnerable. This is
why the 16.3.x line of the advisory is directly exploitable out of the box,
and why the 15.5.x line is also patched defensively (users may pin newer
sharp themselves).

## 7. The Fix (next 15.5.24 / 16.3.3)

```ts
-const BYPASS_TYPES = [SVG, ICO, ICNS, BMP, JXL, HEIC]
+const BYPASS_TYPES = [SVG, ICO, ICNS, BMP, JXL, HEIC, AVIF]
```

and in `getSharp()`:

```ts
_sharp.block({ operation: ['VipsForeignLoad'] })
_sharp.unblock({
  operation: [
    'VipsForeignLoadJpeg',
    'VipsForeignLoadNsgif',
    'VipsForeignLoadPng',
    'VipsForeignLoadSvg',
    'VipsForeignLoadTiff',
    'VipsForeignLoadWebp',
    // 'VipsForeignLoadHeif'  <-- removed (was explicitly unblocked in 16.3.2)
  ],
})
```

Effect: AVIF input is served verbatim (no decode) and every other vips
foreign-load path that could decode AVIF is blocked at the sharp level.
Blur-placeholder generation for static AVIF imports is also disabled
(`VALID_BLUR_EXT = ['jpeg', 'png', 'webp']`).

## 8. PoC Files

| File | Purpose |
|------|---------|
| `poc/gen_poc.py` | Upstream advisory generator (HEVC `hvc1` items) → `poc.avif`; requires ffmpeg + libx265. Used against the ASan libheif build. |
| `poc/gen_poc_av1.py` | AV1 (`av01`) variant → `poc-av1.avif` (128 px primary) and `poc-av1-512.avif` (512 px primary); requires ffmpeg + libaom-av1. Needed for the Next.js path because sharp's bundled libheif has no HEVC decoder, only aom/dav1d. Item payloads are raw aom frame packets extracted from IVF; `av1C` is parsed from the AV1 sequence header OBU. |
| `poc/benign.avif` | Plain 64×64 AV1 still picture (control) |

Both generators write ftyp major brand `avif` so `detectContentType()`
classifies the file as `image/avif` (libheif accepts hvc1/av01 items under an
avif brand via compatible-brand checks).

## 9. Docker Verification Environment

`docker-compose.yml` — three services; app listens on custom port **4300**
inside containers, mapped to **13000**/vuln and **13001**/patched on the host
(host port 3000 is not used):

| Service | Stack | Purpose |
|---------|-------|---------|
| `vuln` | next 16.3.2 + sharp 0.35.3 (libheif 1.23.1), `MALLOC_CHECK_=3` | vulnerable image optimizer |
| `patched` | next 16.3.3 + sharp 0.35.3 (libheif 1.23.1) | fixed image optimizer |
| `asan` | libheif 1.23.1 built with clang AddressSanitizer + heif-dec | deterministic overflow proof |

### Verification results (recorded)

**1. ASan — deterministic heap-buffer-overflow**

```console
$ docker compose run --rm --no-deps asan --quiet /poc/poc.avif /tmp/out.y4m
==1==ERROR: AddressSanitizer: heap-buffer-overflow ...
WRITE of size 2 at 0xffffa0a3620e thread T0
0xffffa0a3620f is located 0 bytes to the right of 16399-byte region [0xffffa0a32200,0xffffa0a3620f)
SUMMARY: AddressSanitizer: heap-buffer-overflow (/src/build/libheif/libheif.so.1+0x33418c)
```

Matches the advisory's expected report (`WRITE of size 2`, 16399-byte
region, `scale_nearest_neighbor()` via `ImageItem::decode_image()`).

**2. Vulnerable next 16.3.2 — unauthenticated process crash**

```console
$ curl "http://localhost:13000/_next/image?url=/benign.avif&w=32&q=75"   # control
http=200 size=323        # source is 309 bytes -> decode+re-encode happened

$ curl "http://localhost:13000/_next/image?url=/poc-av1.avif&w=128&q=75"
(empty reply, curl exit 52)

server logs:
malloc(): invalid size (unsorted)
Aborted
```

A single unauthenticated GET kills the whole Next.js process — heap metadata
corrupted by the ~16 KB OOB write (the 512 px payload corrupts ~256 KB).
The same corruption under libheif 1.23.1 is the primitive the researchers
turned into RCE.

**3. Patched next 16.3.3 — file served verbatim, no decode**

```console
$ curl "http://localhost:13001/_next/image?url=/poc-av1.avif&w=128&q=75"
http=200 size=637 type=image/avif      # bytes identical to source (bypassed)
$ curl "http://localhost:13001/_next/image?url=/poc-av1-512.avif&w=384&q=75"
http=200 size=650                      # bytes identical to source (bypassed)
```

## 10. Impact & Exploitability

- **Attack vector**: network; a single crafted AVIF file, no authentication,
  no user interaction. Only requirement: the app must use (or expose) the
  image optimizer (`/_next/image` is enabled by default).
- **Primitive**: heap buffer overflow — OOB write of 2 bytes per output
  sample, extent and values attacker-controlled (16 KB at 128×128, scalable).
- **Observed**: deterministic ASan-confirmed overflow; glibc heap-corruption
  abort in the production stack; researchers report RCE.
- **Affected deployments**: any self-hosted Next.js image optimizer with
  sharp ≥ 0.35.x (libheif 1.22.0–1.23.1). Managed platforms (Vercel) were
  patched server-side; self-hosted users must upgrade to 15.5.24 / 16.3.3.

## 11. Timeline / Mitigation Status

- 2026-08-25: both advisories published; libheif 1.23.2 and next 15.5.24 /
  16.3.3 released.
- Next.js mitigation is a temporary disable — AVIF optimization will be
  re-enabled once a fixed libheif reaches the sharp prebuilt binaries.
- No CVE assigned to either advisory at the time of writing.

## References

1. https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4
2. https://github.com/strukturag/libheif/security/advisories/GHSA-g89c-p67h-r497
3. Next.js fix: `409772ec807def20132d251ad48fd8d8ad4c73c2`
4. libheif sources: `libheif/image/pixelimage.cc`, `libheif/image-items/image_item.cc`, `libheif/image-items/iden.cc` (v1.23.1, commit `1a3583bc`)
5. libvips: `libvips/foreign/heifload.c` (v8.18.3) — `heif_decode_image()` path
6. sharp prebuilt dependency matrix: https://github.com/lovell/sharp-libvips
