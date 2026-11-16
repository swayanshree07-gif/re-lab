#!/usr/bin/env python3
"""Run the real project and record its output (with timestamps) to docs/media/raw/.
Nothing here is mocked: every line comes from a real process."""
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs/media/raw"); os.makedirs(OUT, exist_ok=True)

def stream(cmd, name, **kw):
    t0 = time.time(); lines = []
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)
    for ln in p.stdout:
        lines.append([round(time.time() - t0, 3), ln.rstrip("\n")])
    rc = p.wait()
    json.dump({"cmd": cmd, "rc": rc, "lines": lines}, open(os.path.join(OUT, name + ".json"), "w"), indent=0)
    return rc, lines

# 1. full demo (clean build + solve all), timestamped
stream(["timeout", "600", "bash", "tools/demo.sh"], "demo")
# 2. extra demo runs for solve-time statistics
for i in range(1, 4):
    stream(["timeout", "300", "bash", "tools/demo.sh"], f"demo_run{i}")
# 3. a player's wrong guesses against a few crackmes (no spoilers shown)
sess = []
for ch, guess in [("01-plain-strcmp", "password123\n"), ("03-xor-single", "letmein\n"),
                  ("08-keygen-name", "alice\n1234-5678\n"), ("28-boss", "hunter2\n")]:
    r = subprocess.run(["timeout", "10", f"dist/{ch}"], cwd=ROOT, input=guess, capture_output=True, text=True)
    sess.append({"ch": ch, "input": guess, "out": r.stdout + r.stderr, "rc": r.returncode})
# 4. solver for challenge 01, as `make test` runs it
r = subprocess.run(["timeout", "60", "python3", "challenges/01-plain-strcmp/solve.py", "dist/01-plain-strcmp"],
                   cwd=ROOT, capture_output=True, text=True)
sess.append({"ch": "solve 01", "out": r.stdout + r.stderr, "rc": r.returncode})
json.dump(sess, open(os.path.join(OUT, "sessions.json"), "w"), indent=1)
# 5. binary facts
facts = []
for f in sorted(os.listdir(os.path.join(ROOT, "dist"))):
    p = os.path.join(ROOT, "dist", f)
    if not os.path.isfile(p): continue
    ft = subprocess.run(["file", "-b", p], capture_output=True, text=True).stdout.strip()
    facts.append({"name": f, "size": os.path.getsize(p), "file": ft})
json.dump(facts, open(os.path.join(OUT, "binaries.json"), "w"), indent=1)
print("captured")
