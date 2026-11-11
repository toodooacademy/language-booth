#!/usr/bin/env python3
"""Copy a generated image into the character folder as a 384px JPEG q80."""
import sys
from pathlib import Path
from PIL import Image

DEST_ROOT = Path("/workspace/language-app/characters")
SIZE = 384
QUALITY = 80

def process(src: str, char_id: str, state: str) -> Path:
    src_path = Path(src)
    dest_dir = DEST_ROOT / char_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{state}.jpg"
    im = Image.open(src_path)
    if im.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", im.size, (245, 237, 224))
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    # center-crop to square if needed
    w, h = im.size
    if w != h:
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        im = im.crop((left, top, left + side, top + side))
    im = im.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    im.save(dest, "JPEG", quality=QUALITY, optimize=True)
    return dest

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: _process.py SRC CHAR_ID STATE", file=sys.stderr)
        sys.exit(2)
    out = process(sys.argv[1], sys.argv[2], sys.argv[3])
    print(out)
