#!/usr/bin/env python3
"""
sort_images.py — Sort images by camera_source XMP tag and filename pattern.

  INFRARED     -> Thermal/
  MAIN_VISIBLE -> RGB/
  *_R.jpg      -> R-JPG/   (radiometric, checked before metadata)
"""

import argparse
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".dng", ".raw", ".nef", ".cr2", ".arw"}

# Matches both element and attribute forms, case-insensitive:
#   <ns:CameraSource>VALUE</ns:CameraSource>
#   camera_source="VALUE"
# Matches radiometric JPG filenames: anything ending in _R.jpg (case-insensitive)
_RJPG_RE = re.compile(r"_R\.jpe?g$", re.IGNORECASE)

_TAG_RE = re.compile(
    rb"camera_?source\s*[=>\"']+\s*([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)

# Only read the first 128 KB — XMP is always near the start of an image file.
_MAX_BYTES = 131_072


def extract_camera_source(path: Path) -> str | None:
    with path.open("rb") as f:
        chunk = f.read(_MAX_BYTES)
    m = _TAG_RE.search(chunk)
    return m.group(1).decode("ascii", errors="replace").upper() if m else None


def process_file(path: Path, thermal_dir: Path, rgb_dir: Path, rjpg_dir: Path, move: bool) -> str:
    # Filename check takes priority — radiometric JPGs are identified by name, not metadata.
    if _RJPG_RE.search(path.name):
        dest_dir = rjpg_dir
    else:
        source = extract_camera_source(path)
        if source == "INFRARED":
            dest_dir = thermal_dir
        elif source == "MAIN_VISIBLE":
            dest_dir = rgb_dir
        else:
            return f"  skip    {path.name}"

    dest = dest_dir / path.name
    if move:
        shutil.move(str(path), dest)
        verb = "moved  "
    else:
        shutil.copy2(path, dest)
        verb = "copied "
    return f"  {verb} {path.name}  ->  {dest_dir.name}/"


def main():
    parser = argparse.ArgumentParser(
        description="Sort images by camera_source XMP tag into Thermal/ and RGB/ folders."
    )
    parser.add_argument("input", help="Folder of images to sort")
    parser.add_argument("-o", "--output", help="Destination folder (default: same as input)")
    parser.add_argument("-m", "--move", action="store_true", help="Move files instead of copying")
    parser.add_argument("-w", "--workers", type=int, default=os.cpu_count(), help="Parallel workers (default: CPU count)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print each file as it is processed")
    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve() if args.output else input_dir

    if not input_dir.is_dir():
        sys.exit(f"error: '{input_dir}' is not a directory")

    thermal_dir = output_dir / "Thermal"
    rgb_dir = output_dir / "RGB"
    rjpg_dir = output_dir / "R-JPG"
    for d in (thermal_dir, rgb_dir, rjpg_dir):
        d.mkdir(parents=True, exist_ok=True)

    skip_dirs = {thermal_dir, rgb_dir, rjpg_dir}
    files = [
        p for p in input_dir.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
        and not any(p.is_relative_to(d) for d in skip_dirs)
    ]

    if not files:
        print("No image files found.")
        return

    print(f"Found {len(files)} image file(s) — processing with {args.workers} worker(s)...")

    thermal, rgb, rjpg, skipped, errors = 0, 0, 0, 0, 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_file, f, thermal_dir, rgb_dir, rjpg_dir, args.move): f for f in files}
        for future in as_completed(futures):
            try:
                result = future.result()
                if "Thermal" in result:
                    thermal += 1
                elif "R-JPG" in result:
                    rjpg += 1
                elif "RGB" in result:
                    rgb += 1
                else:
                    skipped += 1
                if args.verbose:
                    print(result)
            except Exception as exc:
                errors += 1
                print(f"  [error] {futures[future].name}: {exc}", file=sys.stderr)

    op = "Moved" if args.move else "Copied"
    print(f"\nDone.")
    print(f"  {op} to Thermal/ (INFRARED):     {thermal}")
    print(f"  {op} to RGB/     (MAIN_VISIBLE):  {rgb}")
    print(f"  {op} to R-JPG/   (*_R.jpg):       {rjpg}")
    print(f"  Skipped (no match):               {skipped}")
    if errors:
        print(f"  Errors:                           {errors}")


if __name__ == "__main__":
    main()
