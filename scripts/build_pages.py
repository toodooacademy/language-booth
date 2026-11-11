#!/usr/bin/env python3
"""Build a lean GitHub Pages directory from the Language Booth tree.

Ships only runtime assets: referenced audio/images, teacher/narrator clips
(with mouth-timing json), per-language content json, mobile videos, chalkboard.
Drops review/tooling files, dicts/src/masters, video attempts, character
sheets, and word-timing companions for vocab/phrases/smalltalk (play still
works; those clips are fetched per language when a card plays).
"""
from __future__ import annotations

import argparse, json, shutil, sys
from pathlib import Path

LANGS = ("vi", "zh", "ja", "es", "en")
SKIP_DIR_NAMES = {
    "__pycache__", ".git", ".github", "dicts", "_eval", "_refs", "src", "build",
    "attempts", "teacher-takes", "screenshots", "parts", "scripts", "_site", "dist",
}

def is_skipped_dir(parts: tuple[str, ...]) -> bool:
    if any(p in SKIP_DIR_NAMES for p in parts):
        return True
    if "attempts" in parts:
        return True
    if parts[:2] == ("narrator", "samples"):
        return True
    return False

def collect_media_refs(obj, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"mp3", "meta", "image", "img", "src"} and isinstance(v, str) and v and not v.startswith("data:"):
                out.add(v.split("?")[0].lstrip("/"))
            elif k == "audio":
                if isinstance(v, str):
                    out.add(v.split("?")[0].lstrip("/"))
                elif isinstance(v, dict):
                    for vv in v.values():
                        if isinstance(vv, str) and vv.endswith((".mp3", ".json", ".jpg", ".png", ".webp")):
                            out.add(vv.split("?")[0].lstrip("/"))
            else:
                collect_media_refs(v, out)
    elif isinstance(obj, list):
        for it in obj:
            collect_media_refs(it, out)

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def is_required_teacher_clip(rel: Path) -> bool:
    """Roster/system/learn clips used at runtime even if not in audio-index."""
    parts = rel.parts
    if len(parts) < 4 or parts[0] != "audio" or parts[1] != "teacher":
        return False
    folder = parts[3] if len(parts) > 3 else ""
    name = rel.name
    if folder == "learn" and rel.suffix.lower() == ".mp3":
        return True
    if folder == "system" and name.startswith("sys-") and rel.suffix.lower() in {".mp3", ".json"}:
        return True
    if folder == "start" and name.startswith("st-01.") and rel.suffix.lower() in {".mp3", ".json"}:
        return True
    return False

def referenced_paths(root: Path) -> set[str]:
    refs: set[str] = set()
    for p in [
        root / "data" / "audio-index.json",
        root / "data" / "teacher-lines.json",
        root / "data" / "curriculum.json",
        root / "voices.json",
        root / "vocab" / "concepts.json",
        root / "characters" / "frames-index.json",
        root / "characters" / "manifest.json",
        root / "characters" / "roster.json",
    ]:
        if p.exists():
            collect_media_refs(load_json(p), refs)
    for kind in ("vocab", "phrases", "smalltalk"):
        for lang in LANGS:
            p = root / kind / f"{lang}.json"
            if p.exists():
                collect_media_refs(load_json(p), refs)
    # concept images from concepts.json
    concepts = load_json(root / "vocab" / "concepts.json") or {}
    cmap = concepts.get("concepts") or {}
    image_dir = concepts.get("imageDir") or "vocab/img"
    image_ext = (concepts.get("imageExt") or "jpg").lstrip(".")
    for cid, rec in cmap.items():
        if isinstance(rec, dict) and rec.get("image"):
            refs.add(rec["image"].lstrip("/"))
        elif cid:
            refs.add(f"{image_dir}/{cid}.{image_ext}")
    # pair mp3/json so mouth-timing stays with teacher/narrator/lesson clips
    extra=set()
    for r in list(refs):
        if r.endswith(".mp3"):
            extra.add(r[:-4]+".json")
        elif r.endswith(".json") and not r.startswith(("data/","vocab/","phrases/","smalltalk/","characters/")):
            extra.add(r[:-5]+".mp3")
    refs |= extra
    return refs

def keep_rel(rel: Path, refs: set[str], root: Path) -> bool:
    parts = rel.parts
    if not parts or is_skipped_dir(parts):
        return False
    name = rel.name
    if name.startswith(".") and name not in {".nojekyll"}:
        return False
    if name.endswith(".legacy.json") or name in {
        "_prompts.json", "review.json", "review-resolved.json", "review-flags.json",
        "verify-report.json", "teacher-lines.prev.json", "phrases.json",
        "audio.out", "audio.log", "roster-progress.json", "STOP",
        "_sources.json", "_bao_old_sources.json",
    }:
        return False
    if name.startswith("sheet-") and rel.suffix.lower() in {".png", ".jpg"}:
        return False
    if name in {".loudnorm-16.json", "stats.json"}:
        return False
    if rel.suffix.lower() in {".py", ".csv", ".log", ".sh", ".md"}:
        return False
    # video: mobile clips only
    if parts[0] == "video":
        return (
            rel.suffix.lower() == ".mp4"
            and len(parts) >= 4
            and parts[2] == "mobile"
            and parts[3] in {"idle.mp4", "talking.mp4", "meltdown.mp4"}
        )
    if parts[0] == "backgrounds":
        return name == "apply.css" or (len(parts) >= 2 and parts[1] == "chalkboard")
    if parts[0] == "narrator":
        return len(parts) >= 2 and parts[1] == "audio" and rel.suffix.lower() in {".mp3", ".json"}
    if parts[0] == "characters":
        if name in {"manifest.json", "frames-index.json", "align.json", "roster.json"}:
            return True
        return rel.suffix.lower() == ".jpg" and len(parts) >= 2
    if parts[0] == "data":
        return name in {"audio-index.json", "teacher-lines.json", "curriculum.json"}
    if parts[0] == "audio":
        # Only clips the app can actually play (audio-index + roster system/learn).
        if len(parts) >= 2 and parts[1] in {"teacher", "lesson"}:
            if rel.suffix.lower() not in {".mp3", ".json"} or name in {".loudnorm-16.json", "stats.json"}:
                return False
            return rel.as_posix() in refs or is_required_teacher_clip(rel)
        return False
    if parts[0] in {"vocab", "phrases", "smalltalk"}:
        if name in {f"{lang}.json" for lang in LANGS} or name in {"concepts.json", "topics.json"}:
            return True
        if parts[0] == "vocab" and len(parts) >= 2 and parts[1] == "img":
            return rel.suffix.lower() in {".jpg", ".png", ".webp"}
        # Per-language content audio is lazy-fetched from main when hosted on Pages.
        return False
    if rel.as_posix() in {"index.html", "voices.json", ".nojekyll"}:
        return True
    return False

def build(root: Path, out: Path) -> dict:
    refs = referenced_paths(root)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    kept = []
    skipped = 0
    bytes_kept = 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if is_skipped_dir(rel.parts):
            skipped += 1
            continue
        if not keep_rel(rel, refs, root):
            skipped += 1
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        kept.append(rel.as_posix())
        bytes_kept += p.stat().st_size
    # always have .nojekyll so a future legacy builder would stay raw
    (out / ".nojekyll").touch()
    if ".nojekyll" not in kept:
        kept.append(".nojekyll")
    # drop unreferenced content audio if we can match against refs
    # (already included all content mp3s; optional prune)
    pruned = prune_unreferenced_content_audio(out, refs)
    # recount
    files = [p for p in out.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    summary = {
        "files": len(files),
        "bytes": total,
        "mb": round(total / 1e6, 1),
        "skipped_inputs": skipped,
        "pruned_unreferenced_audio": pruned,
        "refs": len(refs),
    }
    print("PAGES_BUILD_META", json.dumps(summary), flush=True)
    return summary

def prune_unreferenced_content_audio(out: Path, refs: set[str]) -> int:
    """If lang JSON provided audio paths, drop content mp3s that nothing references."""
    audio_refs = {r for r in refs if r.endswith(".mp3") and r.split("/")[0] in {"vocab", "phrases", "smalltalk"}}
    if len(audio_refs) < 50:
        return 0  # refs look incomplete; keep all content mp3s
    pruned = 0
    for kind in ("vocab", "phrases", "smalltalk"):
        audio_root = out / kind / "audio"
        if not audio_root.exists():
            continue
        for p in list(audio_root.rglob("*.mp3")):
            rel = p.relative_to(out).as_posix()
            if rel not in audio_refs:
                p.unlink()
                pruned += 1
    return pruned

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    if not (root / "index.html").exists():
        sys.exit(f"no index.html in {root}")
    summary = build(root, out)
    print("PAGES_BUILD", json.dumps(summary))
    # sanity
    for req in [
        out / "index.html",
        out / "backgrounds" / "apply.css",
        out / "narrator" / "audio" / "thay_bao" / "next" / "nx-01.mp3",
        out / "data" / "teacher-lines.json",
        out / "vocab" / "vi.json",
    ]:
        if not req.exists():
            sys.exit(f"missing required {req.relative_to(out)}")
    html = (out / "index.html").read_text(encoding="utf-8", errors="replace")
    if "learn-dock" not in html or "start-lesson" not in html:
        sys.exit("index.html is not the approved learn-layout build")

if __name__ == "__main__":
    main()
