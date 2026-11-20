# News image entry for 19 November 2026 (Python 3.13, standard library only).
# The finished image is entry.png beside this file; this program copies it
# to the grader's output directory. Outside the grader, MAKEFUN_OUTPUT_DIR
# stands in for /output:
#   mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# The image is a fixed asset (variant B: 36 stories, 3 heroes, 15 drawn),
# so this program is fully deterministic and byte-identical on every run.

import os
import shutil
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
src = here / "entry.png"
if not src.is_file():
    sys.exit("entry.png missing beside main.py")
if src.stat().st_size > 1024 * 1024:
    sys.exit("entry.png exceeds the 1 MiB limit")

out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
out_dir.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src, out_dir / "entry.png")
print("entry.png copied (%d bytes)" % src.stat().st_size)
