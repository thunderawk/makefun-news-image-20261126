"""Entrypoint for news-image-20261126.

The image is pre-rendered and committed as entry.png (JPEG, 1024x1024).
This program only validates it and copies it byte-for-byte to the output
directory. Standard library only: the grading sandbox installs nothing.
"""

import hashlib
import os
import shutil
import struct
import sys

MAX_BYTES = 1048576
MAX_DIM = 1024
SOURCE_NAME = "entry.png"


def find_jpeg_size(data):
    """Return (width, height) from the first SOF0/SOF2 marker, or None."""
    pos = 2
    while pos + 1 < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xC0, 0xC2):
            if pos + 9 > len(data):
                return None
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if pos + 4 > len(data):
            return None
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if length < 2:
            return None
        pos += 2 + length
    return None


def validate(data):
    if len(data) < 4:
        raise ValueError("entry.png is too small to be a JPEG")
    if data[0:2] != b"\xff\xd8":
        raise ValueError("entry.png does not start with JPEG SOI marker FFD8")
    if data[-2:] != b"\xff\xd9":
        raise ValueError("entry.png does not end with JPEG EOI marker FFD9")
    if len(data) > MAX_BYTES:
        raise ValueError("entry.png exceeds %d bytes" % MAX_BYTES)
    size = find_jpeg_size(data)
    if size is None:
        raise ValueError("no JPEG SOF0/SOF2 marker found in entry.png")
    width, height = size
    if width > MAX_DIM or height > MAX_DIM:
        raise ValueError("entry.png is %dx%d, over the %d limit"
                         % (width, height, MAX_DIM))
    return width, height


def pick_output_dir():
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        return env_dir
    if os.access("/output", os.W_OK):
        return "/output"
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "out")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)
    with open(source, "rb") as handle:
        data = handle.read()
    width, height = validate(data)
    out_dir = pick_output_dir()
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, SOURCE_NAME)
    shutil.copyfile(source, dest)
    digest = hashlib.sha256(data).hexdigest()
    print("wrote %s %d bytes sha256=%s" % (dest, len(data), digest))
    print("image %dx%d validated" % (width, height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
