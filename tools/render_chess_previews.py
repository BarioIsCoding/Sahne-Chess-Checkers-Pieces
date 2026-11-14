"""Render README chess previews from the canonical chess SVG files.

Dependencies: pip install cairosvg pillow
Run from any directory: python tools/render_chess_previews.py
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PIECES = ROOT / 'chess'
PREVIEWS = PIECES / 'previews'
LIGHT = '#F5F0F1'
DARK = '#EC94A4'
SQUARE = 80
SCALE = 4
BACK_RANK = ('r', 'n', 'b', 'q', 'k', 'b', 'n', 'r')
LINEUP = ('k', 'q', 'r', 'b', 'n', 'p')


@lru_cache(maxsize=None)
def piece_image(name: str) -> Image.Image:
    source = PIECES / f'{name}.svg'
    svg = ET.parse(source).getroot()
    if svg.get('viewBox') != '0 0 100 100':
        raise ValueError(f'Unexpected viewBox: {source}')
    ratio = .95 if name[1] == 'p' else .90
    size = round(SQUARE * SCALE * ratio)
    data = cairosvg.svg2png(url=str(source), output_width=size, output_height=size)
    image = Image.open(BytesIO(data)).convert('RGBA')
    bounds = image.getbbox()
    if bounds is None or min(bounds[:2]) <= 0 or max(bounds[2:]) >= size:
        raise ValueError(f'Artwork has no transparent margin or is clipped: {source}')
    return image


def place(canvas: Image.Image, name: str, col: int, row: int) -> None:
    image = piece_image(name)
    x = col * SQUARE * SCALE + (SQUARE * SCALE - image.width) // 2
    y = row * SQUARE * SCALE + (SQUARE * SCALE - image.height) // 2
    canvas.alpha_composite(image, (x, y))


def save(canvas: Image.Image, name: str, size: tuple[int, int]) -> None:
    result = canvas.convert('RGB').resize(size, Image.Resampling.LANCZOS)
    destination = PREVIEWS / name
    result.save(destination, optimize=True)
    print(f'{destination.relative_to(ROOT)}: {size[0]} x {size[1]}')


def main() -> None:
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    board = Image.new('RGBA', (8 * SQUARE * SCALE,) * 2)
    draw = ImageDraw.Draw(board)
    for row in range(8):
        for col in range(8):
            x, y = col * SQUARE * SCALE, row * SQUARE * SCALE
            draw.rectangle((x, y, x + SQUARE * SCALE - 1, y + SQUARE * SCALE - 1),
                           fill=LIGHT if (row + col) % 2 == 0 else DARK)
    for col, role in enumerate(BACK_RANK):
        place(board, 'b' + role, col, 0)
        place(board, 'w' + role, col, 7)
        place(board, 'bp', col, 1)
        place(board, 'wp', col, 6)
    save(board, 'board.png', (640, 640))

    lineup = Image.new('RGBA', (6 * SQUARE * SCALE, 2 * SQUARE * SCALE), LIGHT)
    ImageDraw.Draw(lineup).rectangle(
        (0, SQUARE * SCALE, lineup.width - 1, lineup.height - 1), fill=DARK)
    for col, role in enumerate(LINEUP):
        place(lineup, 'w' + role, col, 0)
        place(lineup, 'b' + role, col, 1)
    save(lineup, 'set.png', (480, 160))


if __name__ == '__main__':
    main()
