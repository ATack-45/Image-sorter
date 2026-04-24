# image-sorter

Sorts images into **Thermal/** and **RGB/** folders based on the `camera_source`
XMP metadata tag embedded in each image file.

| Tag value      | Destination folder |
| -------------- | ------------------ |
| `INFRARED`     | `Thermal/`         |
| `MAIN_VISIBLE` | `RGB/`             |

Files with no `camera_source` tag are left in place and reported as skipped.

---

## Requirements

**Python 3.10+** — no third-party packages, standard library only.

Check your version:
```
python --version
```

---

## Usage

```
python sort_images.py <input_folder> [options]
```

### Options

| Flag                    | Default          | Description                              |
| ----------------------- | ---------------- | ---------------------------------------- |
| `input`                 | *(required)*     | Folder containing images to sort         |
| `-o`, `--output <dir>`  | same as input    | Where to create `Thermal/` and `RGB/`    |
| `-m`, `--move`          | off (copy)       | Move files instead of copying            |
| `-w`, `--workers <N>`   | CPU core count   | Parallel workers                         |
| `-v`, `--verbose`       | off              | Print each file as it's processed        |

---

## Examples

**Copy images into subfolders inside the same directory:**
```bash
python sort_images.py C:\Drone\Flight01
```
Result:
```
C:\Drone\Flight01\
  Thermal\      <- INFRARED images
  RGB\          <- MAIN_VISIBLE images
  (originals untouched)
```

**Move to a separate output directory:**
```bash
python sort_images.py C:\Drone\Flight01 --output C:\Sorted --move
```

**Verbose output (see every file as it's processed):**
```bash
python sort_images.py C:\Drone\Flight01 --verbose
```

**Limit parallelism (e.g. slow SD card):**
```bash
python sort_images.py /media/sdcard/DCIM --workers 2
```

---

## Supported file types

`.jpg` `.jpeg` `.tif` `.tiff` `.png` `.dng` `.raw` `.nef` `.cr2` `.arw`

---

## How it works

The script reads only the first **128 KB** of each file (XMP metadata is always
near the start of the file) and runs a compiled regex against the raw bytes.
This avoids loading entire multi-megabyte images into memory.

All files are processed in parallel using `ThreadPoolExecutor` — defaulting to
one thread per CPU core, which fully saturates SSDs.

---

## Example output

```
Found 842 image file(s) — processing with 12 worker(s)...

Done.
  Copied to Thermal/ (INFRARED):     421
  Copied to RGB/     (MAIN_VISIBLE):  421
  Skipped (no camera_source tag):     0
```
