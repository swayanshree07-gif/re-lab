#!/usr/bin/env python3
"""Render docs/media/* from the real captures in docs/media/raw/ (see capture.py)."""
import json, os, statistics
from PIL import Image, ImageDraw, ImageFont
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "docs/media/raw"); MED = os.path.join(ROOT, "docs/media")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
BG, FG, GREEN, RED, DIM, CYAN = (24,26,32), (220,220,220), (110,200,120), (235,100,100), (140,140,150), (120,190,230)
load = lambda n: json.load(open(os.path.join(RAW, n)))

def term(lines, title, w=640, rows=None):
    lh = 16; rows = rows or len(lines)
    img = Image.new("RGB", (w, 34 + lh * rows + 8), BG); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 22], fill=(44,46,54))
    for i, c in enumerate([(235,100,100),(230,190,80),(110,200,120)]): d.ellipse([10+i*18, 6, 22+i*18, 18], fill=c)
    d.text((70, 5), title, font=FONT, fill=DIM)
    for i, ln in enumerate(lines[-rows:]):
        col = FG
        if ln.startswith("$"): col = CYAN
        elif "FAILED" in ln or "Wrong" in ln: col = RED
        elif "solved" in ln: col = GREEN
        elif ln.startswith("#"): col = DIM
        d.text((10, 30 + i * lh), ln, font=FONT, fill=col)
    return img

# --- hero GIF: a real `tools/demo.sh` run, replayed at its real pace ---
run = load("demo_run1.json"); lines = [l for l in run["lines"]]
frames, durs, shown, prev = [], [], ["$ make demo"], 0.0
ROWS = 31
frames.append(term(shown, "re-lab — make demo", rows=ROWS)); durs.append(600)
for t, ln in lines:
    shown.append(ln); frames.append(term(shown, "re-lab — make demo", rows=ROWS))
    durs[-1] += int((t - prev) * 1000) if len(durs) > 1 else 0
    durs.append(80); prev = t
durs[-1] = 3000
# cap total at 15 s by scaling the build pause (first line) if needed
tot = sum(durs)
if tot > 15000: durs[1] = max(400, durs[1] - (tot - 15000))
pal = [f.convert("P", palette=Image.ADAPTIVE, colors=16) for f in frames]
pal[0].save(os.path.join(MED, "demo.gif"), save_all=True, append_images=pal[1:], duration=durs, loop=0, optimize=True)

# --- wrong-guess session screenshot ---
sl = []
for s in load("sessions.json"):
    inp = s["input"].strip().replace("\n", " ⏎ ")
    sl += [f"$ ./dist/{s['ch']}", f"  (typed: {inp})", "  " + s["out"].strip(), f"  exit code {s['rc']}", ""]
term(sl[:-1], "re-lab — playing (wrong guesses)").save(os.path.join(MED, "play-session.png"), optimize=True)

# --- solve-time chart (3 real demo runs) ---
runs = [load(f"demo_run{i}.json")["lines"] for i in (1, 2, 3)]
def parse(lines):
    r = {}
    for _, l in lines:
        p = l.split()
        if len(p) == 5 and p[0].isdigit(): r[p[1]] = (p[2], p[3], float(p[4].rstrip("s")))
    return r
P = [parse(r) for r in runs]; names = list(P[0])
stars = [P[0][n][0].count("★") for n in names]
mean = [statistics.mean(p[n][2] for p in P) for n in names]
lo = [mean[i] - min(p[n][2] for p in P) for i, n in enumerate(names)]
hi = [max(p[n][2] for p in P) - mean[i] for i, n in enumerate(names)]
cmap = {1:"#9ecae1",2:"#6baed6",3:"#3182bd",4:"#08519c",5:"#08306b"}
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=100)
ax.bar(range(len(names)), mean, yerr=[lo, hi], color=[cmap[s] for s in stars], capsize=2, ecolor="#888")
ax.set_xticks(range(len(names))); ax.set_xticklabels([n[:2] for n in names])
ax.set_ylabel("solver wall time (s)"); ax.set_xlabel("challenge")
ax.set_title("Automated solver time per challenge — mean of 3 real `make demo` runs (min–max bars)", fontsize=10)
for s, c in cmap.items(): ax.bar([0], [0], color=c, label="★" * s)
ax.legend(title="difficulty", fontsize=8, ncol=5, loc="upper left", frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
fig.savefig(os.path.join(MED, "solve-times.png")); plt.close(fig)

# --- binary size / architecture chart ---
B = [b for b in load("binaries.json") if b["name"][:2].isdigit()]
def arch(f):
    return "RISC-V" if "RISC-V" in f else "AArch64" if "aarch64" in f else "x86-64"
acol = {"x86-64": "#3182bd", "RISC-V": "#e6550d", "AArch64": "#31a354"}
fig, ax = plt.subplots(figsize=(9, 3.6), dpi=100)
ax.bar(range(len(B)), [b["size"]/1024 for b in B], color=[acol[arch(b["file"])] for b in B])
ax.set_xticks(range(len(B))); ax.set_xticklabels([b["name"][:2] for b in B])
ax.set_ylabel("size (KiB)"); ax.set_xlabel("challenge")
ax.set_title("Built crackmes in dist/ — size and target architecture (from `file`)", fontsize=10)
for a, c in acol.items(): ax.bar([0], [0], color=c, label=a)
ax.legend(fontsize=8, frameon=False); ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
fig.savefig(os.path.join(MED, "binaries.png")); plt.close(fig)
print("rendered")
