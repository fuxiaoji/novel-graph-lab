# -*- coding: utf-8 -*-
"""Build X promo posters for Novel Graph Lab from real product screenshots."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROMO = Path(__file__).resolve().parent
F = 'C:/Windows/Fonts/'


def font(name, size):
    return ImageFont.truetype(F + name, size)


def cover_fit(img, w, h, top_trim=0):
    """Trim top fraction, then crop-to-fill resize."""
    if top_trim:
        img = img.crop((0, int(img.size[1] * top_trim), img.size[0], img.size[1]))
    sw, sh = img.size
    scale = max(w / sw, h / sh)
    img = img.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    sw, sh = img.size
    x, y = (sw - w) // 2, (sh - h) // 2
    return img.crop((x, y, x + w, y + h))


def rounded(img, radius):
    mask = Image.new('L', img.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], radius=radius, fill=255)
    out = img.convert('RGBA')
    out.putalpha(mask)
    return out


GOLD = (240, 169, 46)
INK = (13, 21, 32)
PAPER = (247, 248, 250)
MUTED = (139, 150, 164)
LINK = (96, 130, 162)

STATS = [
    ('1.07M-char novel', 'a full public-domain detective novel, verbatim-grounded'),
    ('109 API calls', 'large-context batching for ~1M-token models'),
    ('4 retrieval methods', 'incl. read-a-node, pick-an-edge graph walking'),
    ('Gold-node overlay', 'see exactly which evidence got retrieved'),
]


def base(W, H):
    img = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(img)
    for gx in range(0, W, 44):
        d.line([(gx, 0), (gx, H)], fill=(18, 27, 40), width=1)
    for gy in range(0, H, 44):
        d.line([(0, gy), (W, gy)], fill=(18, 27, 40), width=1)
    return img, d


def paste_shot(img, d, path, sx, sy, w, h, top_trim):
    shot = rounded(cover_fit(Image.open(PROMO / path), w, h, top_trim), 18)
    d.rounded_rectangle([sx - 2, sy - 2, sx + w + 2, sy + h + 2], radius=20, outline=GOLD, width=2)
    img.paste(shot, (sx, sy), shot)


def poster_landscape():
    W, H = 1200, 675
    img, d = base(W, H)
    x = 54
    d.text((x, 46), 'OPEN SOURCE · MIT · PYTHON STDLIB ONLY', font=font('segoeuib.ttf', 16), fill=GOLD)
    d.text((x, 82), 'Novel Graph Lab', font=font('georgiab.ttf', 50), fill=PAPER)
    ty = 82 + 50 + 18
    for i, line in enumerate(['Turn a full detective novel into an', 'evidence graph your agent can interrogate.']):
        d.text((x, ty + i * 31), line, font=font('segoeui.ttf', 21), fill=MUTED)
    sy = ty + 2 * 31 + 30
    for i, (head, sub) in enumerate(STATS):
        yy = sy + i * 62
        d.ellipse([x, yy + 7, x + 10, yy + 17], fill=GOLD)
        d.text((x + 22, yy), head, font=font('segoeuib.ttf', 21), fill=PAPER)
        d.text((x + 22, yy + 25), sub, font=font('segoeui.ttf', 15), fill=MUTED)
    d.text((x, H - 88), 'github.com/fuxiaoji/novel-graph-lab', font=font('segoeuib.ttf', 19), fill=LINK)
    d.text((x, H - 62), 'Live demo — no account, no API key · Installable agent skill', font=font('segoeui.ttf', 14), fill=MUTED)
    paste_shot(img, d, '02-gold-closeup-780x700.png', 588, 44, 570, 400, top_trim=0.06)
    out = PROMO / '04-poster-1200x675.png'
    img.save(out, 'PNG')
    print('saved', out)


def poster_square():
    W, H = 1200, 1200
    img, d = base(W, H)
    x = 64
    d.text((x, 52), 'OPEN SOURCE · MIT · PYTHON STDLIB ONLY', font=font('segoeuib.ttf', 18), fill=GOLD)
    d.text((x, 88), 'Novel Graph Lab', font=font('georgiab.ttf', 62), fill=PAPER)
    ty = 88 + 62 + 20
    for i, line in enumerate(['Turn a full detective novel into an evidence graph', 'your agent can interrogate.']):
        d.text((x, ty + i * 31), line, font=font('segoeui.ttf', 22), fill=MUTED)
    paste_shot(img, d, '01-hero-full-1440x900.png', 64, 250, 1072, 560, top_trim=0.10)
    sy = 846
    for i, (head, sub) in enumerate(STATS):
        col, row = i % 2, i // 2
        xx = x + col * 552
        yy = sy + row * 78
        d.ellipse([xx, yy + 7, xx + 10, yy + 17], fill=GOLD)
        d.text((xx + 22, yy), head, font=font('segoeuib.ttf', 22), fill=PAPER)
        d.text((xx + 22, yy + 27), sub, font=font('segoeui.ttf', 15), fill=MUTED)
    d.text((x, H - 96), 'github.com/fuxiaoji/novel-graph-lab', font=font('segoeuib.ttf', 21), fill=LINK)
    d.text((x, H - 66), 'Live demo — no account, no API key · Installable agent skill', font=font('segoeui.ttf', 15), fill=MUTED)
    out = PROMO / '05-poster-1200x1200.png'
    img.save(out, 'PNG')
    print('saved', out)


poster_landscape()
poster_square()
