#!/usr/bin/env python3
"""news-image-20261120 -- dense newspaper front page for 20 November 2026.

Draws a 1024x1024 PNG front page ("THE WORLD IN ONE IMAGE") in pure
Python 3 standard library: a hand-rolled rasterizer, a 5x7 bitmap font
written out below (each glyph is 7 rows of 5-bit masks), and a minimal
PNG encoder (zlib + struct). No network, no timestamps, no randomness:
two runs write byte-identical output.

Usage: python3 main.py   (writes entry.png to $MAKEFUN_OUTPUT_DIR or /output)
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font -----
# 5x7 bitmap font, written for this entry. Each glyph is 7 rows; each row
# is a 5-bit integer, bit 4 (16) is the leftmost cell, bit 0 (1) the
# rightmost. 0 means an empty row.
FONT = {
    " ": (0, 0, 0, 0, 0, 0, 0),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "a": (0, 0, 0b01110, 0b00001, 0b01111, 0b10001, 0b01111),
    "b": (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b11110),
    "c": (0, 0, 0b01110, 0b10000, 0b10000, 0b10001, 0b01110),
    "d": (0b00001, 0b00001, 0b01111, 0b10001, 0b10001, 0b10001, 0b01111),
    "e": (0, 0, 0b01110, 0b10001, 0b11111, 0b10000, 0b01110),
    "f": (0b00110, 0b01000, 0b01000, 0b11110, 0b01000, 0b01000, 0b01000),
    "g": (0, 0, 0b01110, 0b10001, 0b10001, 0b01111, 0b01110),
    "h": (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    "i": (0b00100, 0, 0b01100, 0b00100, 0b00100, 0b00100, 0b01110),
    "j": (0b00010, 0, 0b00110, 0b00010, 0b00010, 0b00010, 0b01100),
    "k": (0b10000, 0b10000, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010),
    "l": (0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "m": (0, 0, 0b11010, 0b10101, 0b10101, 0b10101, 0b10101),
    "n": (0, 0, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    "o": (0, 0, 0b01110, 0b10001, 0b10001, 0b10001, 0b01110),
    "p": (0, 0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000),
    "q": (0, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001),
    "r": (0, 0, 0b10110, 0b11001, 0b10000, 0b10000, 0b10000),
    "s": (0, 0, 0b01111, 0b10000, 0b01110, 0b00001, 0b11110),
    "t": (0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00100, 0b00110),
    "u": (0, 0, 0b10001, 0b10001, 0b10001, 0b10011, 0b01101),
    "v": (0, 0, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "w": (0, 0, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    "x": (0, 0, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001),
    "y": (0, 0b10001, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    "z": (0, 0, 0b11111, 0b00010, 0b00100, 0b01000, 0b11111),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ";": (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "!": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    "?": (0b01110, 0b10001, 0b00001, 0b00110, 0b00100, 0, 0b00100),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    '"': (0b01010, 0b01010, 0b01010, 0, 0, 0, 0),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "\u2013": (0, 0, 0, 0b01110, 0, 0, 0),
    "\u2014": (0, 0, 0, 0b11111, 0, 0, 0),
    "(": (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ")": (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "&": (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "%": (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    "+": (0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    "=": (0, 0, 0b11111, 0, 0b11111, 0, 0),
    "*": (0, 0b10101, 0b01110, 0b10101, 0, 0, 0),
    "$": (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    "#": (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
    "@": (0b01110, 0b10001, 0b10111, 0b10101, 0b10110, 0b10000, 0b01110),
    "\u2022": (0, 0, 0b01100, 0b01100, 0, 0, 0),
    "\u00b7": (0, 0, 0, 0b01100, 0, 0, 0),
    "[": (0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110),
    "]": (0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110),
    "<": (0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010),
    ">": (0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000),
    "_": (0, 0, 0, 0, 0, 0, 0b11111),
    "~": (0, 0, 0b01001, 0b10110, 0, 0, 0),
    "^": (0b00100, 0b01010, 0b10001, 0, 0, 0, 0),
    "|": (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "`": (0b01000, 0b00100, 0, 0, 0, 0, 0),
    "{": (0b00010, 0b00100, 0b00100, 0b01100, 0b00100, 0b00100, 0b00010),
    "}": (0b01000, 0b00100, 0b00100, 0b00110, 0b00100, 0b00100, 0b01000),
}

# ------------------------------------------------------------- canvas ------
PAPER = (247, 242, 228)
INK = (24, 24, 24)
NAVY = (20, 33, 61)
NAVY2 = (36, 52, 90)
RED = (178, 28, 34)
GOLD = (203, 164, 40)
TEAL = (14, 94, 90)
GREY = (98, 98, 92)
LGREY = (216, 210, 194)
SKY = (60, 86, 130)
ORANGE = (216, 122, 46)
SEA = (22, 50, 82)
WHITE = (250, 248, 242)


class Canvas:
    """A flat RGB raster with rectangle, line, circle, polygon and text ops."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[3 * i] = bg[0]
            self.px[3 * i + 1] = bg[1]
            self.px[3 * i + 2] = bg[2]

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * (y * self.w + x)
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            base = 3 * (yy * self.w + x0)
            for xx in range(x0, x1):
                i = base + 3 * (xx - x0)
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def frame(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def hbar(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vbar(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def seg(self, x0, y0, x1, y1, c, t=1):
        # Bresenham line, t-thick by stamping squares.
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if t == 1:
                self.dot(x0, y0, c)
            else:
                self.fill(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            self.fill(cx - dx, cy + yy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            self.fill(cx - dx, cy + yy, t, 1, c)
            self.fill(cx + dx - t + 1, cy + yy, t, 1, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

    def glyph(self, x, y, ch, scale, c):
        rows = FONT.get(ch, FONT["?"])
        for r, bits in enumerate(rows):
            for col in range(5):
                if bits & (16 >> col):
                    self.fill(x + col * scale, y + r * scale, scale, scale, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, c)
            cx += 6 * scale
        return cx

    def twidth(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_mid(self, x, y, w, s, scale, c):
        self.text(x + (w - self.twidth(s, scale)) // 2, y, s, scale, c)

    def split(self, s, max_chars):
        lines, cur = [], ""
        for wd in s.split(" "):
            if cur and len(cur) + 1 + len(wd) > max_chars:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        return lines

    def block(self, x, y, w, s, scale, c, lh=None):
        max_chars = max(1, w // (6 * scale))
        lh = lh or (8 * scale + 2)
        yy = y
        for ln in self.split(s, max_chars):
            self.text(x, yy, ln, scale, c)
            yy += lh
        return yy


# ---------------------------------------------------------------- png -------
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------- illustrations ---
def draw_summit(cv, x, y, w, h):
    """Kylin Villa, Shenzhen: landscape painting, oval table, three flags."""
    cv.fill(x, y, w, h, NAVY2)
    # painted backdrop: pale mountains under a gold sun
    cv.disc(x + int(w * 0.82), y + int(h * 0.20), 14, GOLD)
    cv.poly([(x, y + int(h * 0.55)), (x + int(w * 0.30), y + int(h * 0.22)),
             (x + int(w * 0.55), y + int(h * 0.55))], (96, 116, 150))
    cv.poly([(x + int(w * 0.40), y + int(h * 0.55)),
             (x + int(w * 0.68), y + int(h * 0.30)),
             (x + w, y + int(h * 0.55))], (76, 96, 132))
    cv.fill(x, y + int(h * 0.55), w, h - int(h * 0.55), (52, 66, 96))
    # three flags on poles behind the table
    poles = ((0.16, (178, 34, 52)), (0.50, (222, 32, 32)),
             (0.84, (28, 58, 148)))
    for fx, col in poles:
        px = x + int(w * fx)
        cv.vbar(px, y + 8, int(h * 0.42), INK, 2)
        cv.fill(px + 2, y + 10, 34, 20, col)
        if fx == 0.16:  # US stripes
            for sy in range(y + 10, y + 30, 4):
                cv.hbar(px + 2, sy, 34, WHITE, 2)
            cv.fill(px + 2, y + 10, 14, 10, NAVY)
        elif fx == 0.50:  # China stars
            cv.disc(px + 11, y + 20, 3, GOLD)
            cv.disc(px + 24, y + 15, 2, GOLD)
            cv.disc(px + 27, y + 22, 2, GOLD)
        else:  # Russia tricolour
            cv.fill(px + 2, y + 10, 34, 7, WHITE)
            cv.fill(px + 2, y + 17, 34, 6, (30, 80, 190))
            cv.fill(px + 2, y + 23, 34, 7, RED)
    # oval table (flat trapezoid, kept inside the box)
    ty = y + int(h * 0.68)
    cv.poly([(x + 28, ty), (x + w - 28, ty),
             (x + w - 8, ty + 24), (x + 8, ty + 24)], (128, 90, 52))
    cv.fill(x + 28, ty, w - 56, 6, (150, 108, 64))
    # orchid centrepiece on the table
    cv.disc(x + w // 2, ty + 13, 5, (232, 190, 220))
    cv.disc(x + w // 2 - 11, ty + 14, 3, (232, 190, 220))
    cv.disc(x + w // 2 + 11, ty + 14, 3, (232, 190, 220))
    # three seated figures behind the table
    for fx, suit in ((0.24, NAVY), (0.50, (60, 60, 60)), (0.76, NAVY)):
        fx0 = x + int(w * fx)
        cv.disc(fx0, ty - 26, 12, (232, 200, 170))          # head
        cv.poly([(fx0 - 19, ty - 12), (fx0 + 19, ty - 12),
                 (fx0 + 25, ty + 2), (fx0 - 25, ty + 2)], suit)


def draw_kyiv(cv, x, y, w, h):
    """Kyiv at night: river, a bridge with a broken span, flak bursts."""
    cv.fill(x, y, w, h, (16, 20, 38))
    # stars
    for sx, sy in ((0.08, 0.10), (0.24, 0.06), (0.40, 0.14), (0.58, 0.08),
                   (0.72, 0.16), (0.90, 0.08), (0.32, 0.24), (0.66, 0.26)):
        cv.fill(x + int(w * sx), y + int(h * sy), 3, 3, WHITE)
    # river
    ry = y + int(h * 0.62)
    cv.fill(x, ry, w, h - int(h * 0.62), (28, 52, 84))
    for wy in range(ry + 8, y + h - 4, 12):
        cv.hbar(x + 8, wy, w - 16, (52, 96, 140), 2)
    # city silhouette on the far bank
    for bx, bw, bh in ((0.04, 0.10, 0.30), (0.18, 0.08, 0.38),
                       (0.30, 0.12, 0.26), (0.70, 0.10, 0.34),
                       (0.84, 0.12, 0.28)):
        cv.fill(x + int(w * bx), ry - int(h * bh), int(w * bw),
                int(h * bh), (10, 14, 28))
        for wy in range(ry - int(h * bh) + 6, ry - 4, 10):
            for wx in range(x + int(w * bx) + 3,
                            x + int(w * bx) + int(w * bw) - 3, 8):
                if (wx + wy) % 4 == 0:
                    cv.fill(wx, wy, 2, 3, GOLD)
    # bridge deck, left and right of the gap
    dy = y + int(h * 0.44)
    cv.fill(x, dy, int(w * 0.36), 7, (150, 150, 146))
    cv.fill(x + int(w * 0.64), dy, int(w * 0.36), 7, (150, 150, 146))
    cv.fill(x + int(w * 0.08), dy + 7, 7, ry - dy - 7, (110, 110, 106))
    cv.fill(x + int(w * 0.90), dy + 7, 7, ry - dy - 7, (110, 110, 106))
    # fallen span, tilted into the river
    cv.poly([(x + int(w * 0.38), dy + 2), (x + int(w * 0.56), dy + 16),
             (x + int(w * 0.54), dy + 24), (x + int(w * 0.36), dy + 10)],
            (110, 110, 106))
    # flak bursts over the gap
    for ex, ey in ((0.44, 0.26), (0.58, 0.20)):
        cxp, cyp = x + int(w * ex), y + int(h * ey)
        for dx, dy2 in ((1, 0), (-1, 0), (0, 1), (0, -1),
                        (1, 1), (-1, -1), (1, -1), (-1, 1)):
            cv.seg(cxp, cyp, cxp + dx * 13, cyp + dy2 * 13, ORANGE, 2)
        cv.disc(cxp, cyp, 5, WHITE)
        cv.disc(cxp, cyp, 9, (232, 164, 80))
    # searchlight beams
    cv.seg(x + int(w * 0.12), ry, x + int(w * 0.30), y + 6, (220, 220, 180), 2)
    cv.seg(x + int(w * 0.88), ry, x + int(w * 0.72), y + 6, (220, 220, 180), 2)


def draw_markets(cv, x, y, w, h):
    """Falling market: red bars stepping down, dashed trend, down arrow."""
    cv.fill(x, y, w, h, (30, 30, 34))
    base = y + h - 8
    bars = (0.72, 0.64, 0.55, 0.62, 0.44, 0.36, 0.24)
    bw = w // 9
    for i, f in enumerate(bars):
        bx = x + 6 + i * (bw + 2)
        bh = int((h - 22) * f)
        cv.fill(bx, base - bh, bw, bh, RED if i >= 4 else (120, 40, 44))
    # dashed falling trend line
    pts = []
    for i, f in enumerate(bars):
        pts.append((x + 6 + i * (bw + 2) + bw // 2,
                    base - int((h - 22) * f) - 6))
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        for t in range(0, 10, 2):
            fx = x0 + (x1 - x0) * t // 10
            fy = y0 + (y1 - y0) * t // 10
            cv.fill(fx, fy, 3, 3, GOLD)
    # down arrow at the end
    ax, ay = x + w - 16, y + int(h * 0.72)
    cv.seg(ax, ay - 26, ax, ay + 6, WHITE, 3)
    cv.poly([(ax - 9, ay - 2), (ax + 9, ay - 2), (ax, ay + 14)], WHITE)
    cv.fill(x, base, w, 2, WHITE)


def draw_cyclone(cv, x, y, w, h):
    """Cyclone Akvan: spiral bands over the sea, rain, coastline."""
    cv.fill(x, y, w, h, (58, 84, 118))
    # sea
    cv.fill(x, y + int(h * 0.55), w, h - int(h * 0.55), SEA)
    # coastline
    cv.poly([(x, y + h), (x, y + int(h * 0.62)),
             (x + int(w * 0.35), y + int(h * 0.55)),
             (x + int(w * 0.42), y + int(h * 0.70)),
             (x + int(w * 0.30), y + h)], (196, 178, 140))
    # spiral bands
    cxp, cyp = x + int(w * 0.62), y + int(h * 0.38)
    for r, col in ((44, WHITE), (36, (220, 226, 232)),
                   (28, WHITE), (20, (190, 200, 212)), (12, WHITE)):
        cv.ring(cxp, cyp, r, col, 4)
    cv.disc(cxp, cyp, 7, NAVY)
    # rain streaks
    for rx, ry, rl in ((0.10, 0.12, 14), (0.22, 0.06, 12), (0.34, 0.16, 14),
                       (0.48, 0.08, 12), (0.80, 0.12, 14), (0.90, 0.22, 12),
                       (0.16, 0.30, 12), (0.86, 0.34, 14)):
        sx, sy = x + int(w * rx), y + int(h * ry)
        cv.seg(sx, sy, sx - 4, sy + rl, (190, 205, 225), 2)
    # shelter roofs on the coast
    for hx in (0.06, 0.16, 0.26):
        hx0 = x + int(w * hx)
        hy0 = y + int(h * 0.72)
        cv.poly([(hx0, hy0), (hx0 + 10, hy0 - 8), (hx0 + 20, hy0)],
                (178, 40, 40))
        cv.fill(hx0 + 2, hy0, 16, 8, (240, 236, 222))


# ----------------------------------------------------------------- page ------
GRID = [
    ("GAZA", "TROOPS CROSS YELLOW LINE"),
    ("RIYADH", "HOUTHI MISSILE HITS PIF TOWER"),
    ("EU-UK", "SUMMIT OPENS IN BRUSSELS"),
    ("GERMANY", "MERZ: NO NEW YALTA"),
    ("DENMARK", "GREENLAND-US DEAL APPROVED"),
    ("POLAND", "AIRSPACE VIOLATIONS PROBED"),
    ("ESTONIA", "BORDER WITH RUSSIA TO SHUT"),
    ("HAITI", "34 GANG MEMBERS KILLED"),
    ("EL SALVADOR", "BUKELE SEEKS THIRD TERM"),
    ("S AMERICA", "US-VENEZUELA DEAL SIGNED"),
    ("SENEGAL", "MIGRANT BOAT CAPSIZES"),
    ("SUDAN", "10 KILLED AT GOLD MINE"),
    ("SOMALIA", "UAE ENVOY ORDERED OUT"),
    ("COP31", "DRAFT DROPS FOSSIL FUELS"),
    ("KENYA", "LAST EBOLA PATIENT OUT"),
    ("S KOREA", "FIRST CHOLERA CASE IN DECADE"),
    ("TAIWAN", "2,700 ACCOUNTS FLAGGED"),
    ("USA", "CYBER CHIEF FIRED"),
    ("SPACE", "VOYAGER 1: 1-DAY SIGNAL"),
    ("SPORT", "ALCARAZ 3-0, MEDVEDEV WINS"),
]

TIMELINE = [
    ("02:00", "AKVAN LANDS", "ODISHA"),
    ("~01:00", "KYIV HIT", "BRIDGES"),
    ("~09:00", "EU-UK SUMMIT", "BRUSSELS"),
    ("~12:00", "COP31 DRAFT", "FOSSIL FUELS"),
    ("~14:30", "MARKETS -5.2%", "NASDAQ"),
    ("~19:00", "MEDVEDEV WINS", "SEMIS"),
]


def build():
    cv = Canvas(W, H, PAPER)
    cv.fill(0, 0, W, H, NAVY)
    cv.fill(8, 8, W - 16, H - 16, PAPER)

    # ---- masthead ------------------------------------------------------
    cv.fill(8, 8, W - 16, 92, NAVY)
    cv.text(24, 26, "VOL. I", 2, GOLD)
    cv.text(W - 24 - cv.twidth("LATE EDITION", 2), 26, "LATE EDITION", 2, GOLD)
    cv.text_mid(8, 20, W - 16, "THE WORLD IN ONE IMAGE", 5, WHITE)
    cv.fill(182, 66, 660, 2, GOLD)
    cv.text_mid(8, 74, W - 16, "FRIDAY, 20 NOVEMBER 2026", 3, GOLD)

    # ---- kicker --------------------------------------------------------
    cv.text_mid(8, 108, W - 16,
                "FRONT PAGE - EVERY STORY FIRST REPORTED TODAY", 2, RED)

    # ---- lead: Shenzhen, the day after ---------------------------------
    draw_summit(cv, 12, 130, 336, 172)
    cv.text(12, 306, "THE TRILATERAL, A DAY ON", 2, GREY)
    tx = 364
    cv.text(tx, 130, "DIPLOMACY - SHENZHEN AFTERMATH", 2, RED)
    cv.text(tx, 152, "THREE LEADERS,", 5, INK)
    cv.text(tx, 192, "ONE DECLARATION", 5, INK)
    cv.block(tx, 236, 644,
             "Trump, Xi and Putin sign a four-point joint declaration "
             "after their first three-way meeting: a nuclear war 'cannot "
             "be won and must never be fought'. No arms deal, no Ukraine "
             "settlement - and Europe answers back.",
             2, INK)
    cv.hbar(8, 326, W - 16, NAVY, 3)

    # ---- row 2: Kyiv / markets -----------------------------------------
    y2 = 334
    draw_kyiv(cv, 12, y2, 120, 140)
    cv.text(144, y2, "UKRAINE - KYIV", 2, RED)
    cv.text(144, y2 + 24, "KYIV BRIDGES", 3, INK)
    cv.text(144, y2 + 48, "HIT OVERNIGHT", 3, INK)
    cv.block(144, y2 + 76, 360,
             "Overnight strikes hit three Dnipro bridges; three dead, "
             "15 hurt. Ukraine drones hit a plant in Smolensk.",
             2, INK, lh=16)
    cv.vbar(508, y2, 140, LGREY, 2)

    draw_markets(cv, 520, y2, 120, 140)
    cv.text(652, y2, "MARKETS - FRIDAY", 2, RED)
    cv.text(652, y2 + 24, "STOCKS PLUNGE", 3, INK)
    cv.text(652, y2 + 48, "IN AI ROUT", 3, INK)
    cv.block(652, y2 + 76, 360,
             "S&P 500 falls 3.7%, a seventh straight loss; Nasdaq drops "
             "5.2%. Nvidia sheds 14%; Anthropic slides 9%.",
             2, INK, lh=16)
    cv.hbar(8, 486, W - 16, NAVY, 3)

    # ---- row 3: Akvan / ICJ --------------------------------------------
    y3 = 494
    draw_cyclone(cv, 12, y3, 120, 124)
    cv.text(144, y3, "WEATHER - INDIA", 2, RED)
    cv.text(144, y3 + 22, "AKVAN HITS", 3, INK)
    cv.text(144, y3 + 44, "ODISHA COAST", 3, INK)
    cv.block(144, y3 + 70, 360,
             "Akvan crosses near Gopalpur at 02:00 UTC. 300,000 "
             "evacuated; no deaths reported.",
             2, INK, lh=15)
    cv.vbar(508, y3, 124, LGREY, 2)

    cv.text(520, y3, "JUSTICE - THE HAGUE", 2, RED)
    cv.text(520, y3 + 22, "MYANMAR: THE", 3, INK)
    cv.text(520, y3 + 44, "DAY AFTER", 3, INK)
    cv.block(520, y3 + 70, 488,
             "A day after the ICJ found Myanmar guilty of genocide, "
             "pressure grows for reparations. Over a million Rohingya "
             "remain displaced.",
             2, INK, lh=15)
    cv.hbar(8, 632, W - 16, NAVY, 3)

    # ---- timeline ------------------------------------------------------
    yt = 640
    cv.text(12, yt, "THE DAY IN UTC", 2, RED)
    cv.text(W - 12 - cv.twidth("TIMES APPROXIMATE", 2), yt,
            "TIMES APPROXIMATE", 2, GREY)
    cv.hbar(12, yt + 30, W - 24, NAVY, 2)
    slot = (W - 24) // len(TIMELINE)
    for i, (tm, l1, l2) in enumerate(TIMELINE):
        cxp = 12 + slot * i + slot // 2
        cv.disc(cxp, yt + 31, 5, RED)
        cv.text_mid(12 + slot * i, yt + 42, slot, tm, 2, INK)
        cv.text_mid(12 + slot * i, yt + 58, slot, l1, 2, INK)
        cv.text_mid(12 + slot * i, yt + 74, slot, l2, 2, INK)
    cv.hbar(8, 736, W - 16, NAVY, 3)

    # ---- story grid ----------------------------------------------------
    yg = 744
    cv.text(12, yg, "MORE OF THE DAY - IN BRIEF", 2, RED)
    cv.text(W - 12 - cv.twidth("20 STORIES", 2), yg, "20 STORIES", 2, GREY)
    cols, rows = 5, 4
    gw = (W - 24 - (cols - 1) * 12) // cols
    gh = 44
    gy0 = yg + 24
    for idx, (tag, head) in enumerate(GRID):
        r, c = divmod(idx, cols)
        gx = 12 + c * (gw + 12)
        gy = gy0 + r * gh
        cv.text(gx, gy, tag, 1, RED)
        lines = cv.split(head, max(1, gw // 12))
        yy = gy + 10
        for ln in lines[:2]:
            cv.text(gx, yy, ln, 2, INK)
            yy += 15
    cv.hbar(8, 948, W - 16, NAVY, 3)

    # ---- footer: date check + also reported ----------------------------
    yf = 956
    cv.frame(12, yf, 348, 52, RED, 3)
    cv.text(24, yf + 4, "DATE CHECK", 2, RED)
    cv.text(24, yf + 20, "TODAY IS FRIDAY", 2, INK)
    cv.text(24, yf + 35, "20 NOVEMBER 2026.", 2, INK)
    cv.text(372, yf, "ALSO REPORTED TODAY:", 2, RED)
    cv.block(372, yf + 18, 640,
             "Kerch rail resumes - GTA VI tops $2bn - Fiona the hippo "
             "dies - NYC to close Rikers by 2032.",
             2, INK)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
