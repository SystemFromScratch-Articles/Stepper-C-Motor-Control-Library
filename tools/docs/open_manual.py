#!/usr/bin/env python3
"""Open the PDF manual built by build_manual.py in the default PDF viewer.

Used by the VS Code task "Docs: Build and open PDF manual". The file name is read from
extra.manual.output in mkdocs.yml, exactly as build_manual.py does.
"""

import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_manual import library_version, load_mkdocs  # noqa: E402


def main() -> int:
    manual = (load_mkdocs().get("extra") or {}).get("manual") or {}
    pattern = manual.get("output", "build/manual/User_Manual_v{version}.pdf")
    pdf = os.path.join(ROOT, pattern.format(version=library_version(manual)))
    if not os.path.isfile(pdf):
        print(f"{pdf} not found; run the task 'Docs: Build PDF manual' first.", file=sys.stderr)
        return 1
    print(f"opening {pdf}")
    if sys.platform.startswith("win"):
        os.startfile(pdf)  # noqa: S606 (Windows only)
    elif sys.platform == "darwin":
        subprocess.run(["open", pdf], check=False)
    else:
        subprocess.run(["xdg-open", pdf], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
