#!/usr/bin/env python3
"""Loudness match (gain + true-peak-safe limiter) for lesson content clips (vocab/phrases/smalltalk + teacher learn prompts).
Target -16 LUFS integrated, true peak ceiling -1.5 dBTP. Audio level only; wording untouched."""
import subprocess, re, json, sys, os, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT = Path("/workspace/language-app")
BACKUP = Path("/workspace/backups/language-app-content-audio-prenorm-2026-11-11")
TARGET, CEIL = -16.0, -1.5
def measure(p):
    r = subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(p),"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    I = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", s); P = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", s)
    f = lambda m: float(m.group(1)) if m and m.group(1)!="-inf" else None
    return f(I), f(P)
def loudnorm_measure(src):
    r = subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(src),"-af",f"loudnorm=I={TARGET}:TP={CEIL}:LRA=11:print_format=json","-f","null","-"],capture_output=True,text=True)
    return json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}")+1])
def work(p):
    rel = p.relative_to(ROOT).as_posix()
    b0 = BACKUP / rel
    src = b0 if b0.exists() else p
    I, P = measure(src)
    if I is None or I < -60 or P is None:
        return {"f": rel, "I": I, "P": P, "skip": "unmeasurable"}
    g = TARGET - I
    if abs(g) < 0.5 and P <= CEIL:
        return {"f": rel, "I": I, "P": P, "skip": "close"}
    b = BACKUP / rel
    if not b.exists():
        b.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, b)
    tmp = p.with_suffix(".norm.mp3")
    # loudnorm is unreliable on 1-3 s clips; use gain + oversampled peak limiter (ceiling about -1.9 dBFS)
    af = f"aresample=96000,volume={g:.2f}dB,alimiter=limit=0.80:attack=1:release=50:level=false,aresample=24000"
    r = subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(b),"-af",af,"-c:a","libmp3lame","-b:a","32k","-ar","24000","-ac","1","-map_metadata","-1",str(tmp)],capture_output=True,text=True)
    if r.returncode: return {"f": rel, "err": r.stderr[-200:]}
    os.replace(tmp, p)
    I2, P2 = measure(p)
    return {"f": rel, "I": I, "P": P, "gain": round(g,2), "I2": I2, "P2": P2}
files = []
for d in ["vocab/audio","phrases/audio","smalltalk/audio"]:
    files += sorted((ROOT/d).rglob("*.mp3"))
files += sorted(ROOT.glob("audio/teacher/*/learn/*.mp3"))
files = [f for f in files if not f.name.endswith(".norm.mp3")]
print("files", len(files), flush=True)
out = []
with ThreadPoolExecutor(8) as ex:
    for i, res in enumerate(ex.map(work, files)):
        out.append(res)
        if i % 1000 == 0: print(i, res, flush=True)
json.dump(out, open(ROOT/"audio"/"normalize-content-2026-11-11.json","w"), indent=0)
n = [r for r in out if "gain" in r]
print("done", len(out), "changed", len(n), "skipped", sum(1 for r in out if "skip" in r), "errors", sum(1 for r in out if "err" in r), flush=True)
