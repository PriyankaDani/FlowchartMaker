"""One-off generator for the vision-chain Ollama test fixtures (checked into
tests/parsing/fixtures/). Re-run only if the fixtures need to change.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "parsing" / "fixtures"

# A vision model's encoder downsamples the input (llava resizes to ~336x336 internally) --
# PIL's default ~11px bitmap font is illegible after that resize, which pushed the model to
# hallucinate plausible-looking content instead of grounding on the actual pixels. Large,
# bold text and thick strokes keep the sketch legible post-downsample.
_FONT = ImageFont.load_default(size=36)


def _text_size(draw: ImageDraw.ImageDraw, text: str) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=_FONT)
    return right - left, bottom - top


def draw_clean_sketch() -> Image.Image:
    """Matches the worked example in docs/learning/example.md:
    Start -> Check email -> Urgent? -(Yes)-> Reply now -> End
                                  \\-(No)-> Add to queue -> End
    """
    img = Image.new("RGB", (1400, 1100), "white")
    draw = ImageDraw.Draw(img)

    def centered_text(cx, cy, text):
        w, h = _text_size(draw, text)
        draw.text((cx - w / 2, cy - h / 2), text, fill="black", font=_FONT)

    def stadium(cx, cy, text):
        draw.rounded_rectangle([cx - 130, cy - 40, cx + 130, cy + 40], radius=40, outline="black", width=6)
        centered_text(cx, cy, text)

    def box(cx, cy, text):
        draw.rectangle([cx - 150, cy - 40, cx + 150, cy + 40], outline="black", width=6)
        centered_text(cx, cy, text)

    def diamond(cx, cy, text):
        draw.polygon(
            [(cx, cy - 70), (cx + 150, cy), (cx, cy + 70), (cx - 150, cy)],
            outline="black",
            width=6,
        )
        centered_text(cx, cy, text)

    def arrow(x1, y1, x2, y2, label=None):
        draw.line([(x1, y1), (x2, y2)], fill="black", width=6)
        draw.polygon(
            [(x2, y2), (x2 - 14, y2 - 14), (x2 - 14, y2 + 14)]
            if x1 < x2
            else [(x2, y2), (x2 + 14, y2 - 14), (x2 + 14, y2 + 14)],
            fill="black",
        )
        if label:
            centered_text((x1 + x2) // 2, (y1 + y2) // 2 - 25, label)

    stadium(700, 90, "Start")
    box(700, 250, "Check email")
    diamond(700, 440, "Urgent?")
    box(380, 650, "Reply now")
    box(1020, 650, "Add to queue")
    stadium(700, 850, "End")

    arrow(700, 130, 700, 210)
    arrow(700, 290, 700, 370)
    arrow(620, 500, 420, 610, "Yes")
    arrow(780, 500, 980, 610, "No")
    arrow(430, 690, 650, 810)
    arrow(970, 690, 750, 810)

    return img


def draw_messy_scribble() -> Image.Image:
    img = Image.new("RGB", (1400, 1100), "white")
    draw = ImageDraw.Draw(img)
    random.seed(42)
    for _ in range(80):
        x1, y1 = random.randint(0, 1400), random.randint(0, 1100)
        x2, y2 = x1 + random.randint(-100, 100), y1 + random.randint(-100, 100)
        draw.line([(x1, y1), (x2, y2)], fill="black", width=4)
    return img


def draw_blank_page() -> Image.Image:
    return Image.new("RGB", (900, 700), "white")


if __name__ == "__main__":
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    draw_clean_sketch().save(FIXTURES_DIR / "clean_sketch.png")
    draw_messy_scribble().save(FIXTURES_DIR / "messy_scribble.png")
    draw_blank_page().save(FIXTURES_DIR / "blank_page.png")
    print(f"Fixtures written to {FIXTURES_DIR}")
