#!/usr/bin/env python3
"""Turn any image into the square assets/portrait.jpg the site expects.

    python3 tools/make_portrait.py <source-image> [--size 900] [--bias 0.35]

Trims uniform borders (the white bars press layouts often leave), crops to a
square, and writes assets/portrait.jpg.  --bias sets where the square sits
vertically in a tall image: 0 = top, 0.5 = centre.  Faces usually sit high, so
the default leans upward.

Uses sips (built into macOS) to decode and re-encode, and pure Python in
between, so there is nothing to install.  On Windows, open the source in any
image editor and export a square JPEG to assets/portrait.jpg instead.
"""
import argparse
import os
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)


def sips(*args):
    subprocess.run(['sips', *args], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def read_png(path):
    """Decode an 8-bit RGB/RGBA PNG to (width, height, channels, bytearray)."""
    raw = open(path, 'rb').read()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit('not a PNG: %s' % path)
    pos, idat, w = 8, [], None
    while pos < len(raw):
        ln, typ = struct.unpack('>I4s', raw[pos:pos + 8])
        body = raw[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, depth, color = struct.unpack('>IIBB', body[:10])
            if depth != 8 or color not in (2, 6):
                raise SystemExit('need an 8-bit RGB/RGBA PNG, got depth=%d color=%d'
                                 % (depth, color))
            ch = 3 if color == 2 else 4
        elif typ == b'IDAT':
            idat.append(body)
        elif typ == b'IEND':
            break
        pos += 12 + ln

    data = zlib.decompress(b''.join(idat))
    stride = w * ch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    src = 0
    for y in range(h):
        ft = data[src]; src += 1
        line = bytearray(data[src:src + stride]); src += stride
        if ft == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                left = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise SystemExit('unknown PNG filter %d' % ft)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def write_png(path, w, h, ch, px):
    stride = w * ch
    rows = bytearray()
    for y in range(h):
        rows.append(0)
        rows += px[y * stride:(y + 1) * stride]
    color = 2 if ch == 3 else 6

    def chunk(typ, body):
        return (struct.pack('>I', len(body)) + typ + body +
                struct.pack('>I', zlib.crc32(typ + body) & 0xFFFFFFFF))

    with open(path, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n')
        fh.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, color, 0, 0, 0)))
        fh.write(chunk(b'IDAT', zlib.compress(bytes(rows), 9)))
        fh.write(chunk(b'IEND', b''))


def trim_uniform_border(w, h, ch, px, tol=10):
    """Drop rows/columns that are a single flat colour (letterbox bars)."""
    def flat_col(x):
        r0, g0, b0 = px[x * ch], px[x * ch + 1], px[x * ch + 2]
        for y in range(0, h, max(1, h // 120)):
            i = (y * w + x) * ch
            if (abs(px[i] - r0) > tol or abs(px[i + 1] - g0) > tol
                    or abs(px[i + 2] - b0) > tol):
                return False
        return True

    def flat_row(y):
        i0 = y * w * ch
        r0, g0, b0 = px[i0], px[i0 + 1], px[i0 + 2]
        for x in range(0, w, max(1, w // 120)):
            i = (y * w + x) * ch
            if (abs(px[i] - r0) > tol or abs(px[i + 1] - g0) > tol
                    or abs(px[i + 2] - b0) > tol):
                return False
        return True

    x0, x1, y0, y1 = 0, w - 1, 0, h - 1
    while x0 < x1 and flat_col(x0): x0 += 1
    while x1 > x0 and flat_col(x1): x1 -= 1
    while y0 < y1 and flat_row(y0): y0 += 1
    while y1 > y0 and flat_row(y1): y1 -= 1
    return x0, y0, x1 - x0 + 1, y1 - y0 + 1


def crop(w, h, ch, px, bx, by, bw, bh):
    out = bytearray(bw * bh * ch)
    for y in range(bh):
        s = ((by + y) * w + bx) * ch
        out[y * bw * ch:(y + 1) * bw * ch] = px[s:s + bw * ch]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('--size', type=int, default=900)
    ap.add_argument('--bias', type=float, default=0.35,
                    help='vertical position of the square, 0=top 0.5=centre')
    ap.add_argument('--no-trim', action='store_true')
    ap.add_argument('--rect', help='explicit crop region "x,y,w,h" in source '
                                   'pixels; skips auto-trim and bias')
    ap.add_argument('--out', default=os.path.join(PROJECT, 'assets', 'portrait.jpg'))
    a = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix='portrait-')
    flat = os.path.join(tmp, 'in.png')
    sips('-s', 'format', 'png', a.source, '--out', flat)

    w, h, ch, px = read_png(flat)

    if a.rect:
        rx, ry, rw, rh = (int(v) for v in a.rect.split(','))
        if rx < 0 or ry < 0 or rx + rw > w or ry + rh > h:
            raise SystemExit('--rect %s does not fit inside %dx%d' % (a.rect, w, h))
        px = crop(w, h, ch, px, rx, ry, rw, rh)
        w, h = rw, rh
        print('rect crop %dx%d at (%d,%d)' % (rw, rh, rx, ry))
        a.no_trim = True

    if not a.no_trim:
        bx, by, bw, bh = trim_uniform_border(w, h, ch, px)
        if (bw, bh) != (w, h):
            print('trimmed border -> %dx%d at (%d,%d)' % (bw, bh, bx, by))
            px = crop(w, h, ch, px, bx, by, bw, bh)
            w, h = bw, bh

    side = min(w, h)
    sx = (w - side) // 2
    sy = int((h - side) * a.bias)
    px = crop(w, h, ch, px, sx, sy, side, side)
    print('square crop %dx%d at (%d,%d)' % (side, side, sx, sy))

    sq = os.path.join(tmp, 'sq.png')
    write_png(sq, side, side, ch, px)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    sips('-z', str(a.size), str(a.size), '-s', 'format', 'jpeg',
         '-s', 'formatOptions', '82', sq, '--out', a.out)
    print('wrote %s (%d bytes)' % (a.out, os.path.getsize(a.out)))


if __name__ == '__main__':
    main()
