from enum import Enum
from math import ceil
from typing import Literal
from PIL import Image, ImageFont, ImageDraw
from pilmoji.core import Pilmoji
from string import ascii_letters
from pathlib import Path


MAX_WIDTH = 512
# font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
# font_path = "OpenSans-VariableFont_wdth,wght.ttf"
font_path = Path(__file__).parent / "OpenSans-VariableFont_wdth,wght.ttf"
FONT = ImageFont.truetype(font_path, 48)
FONT_LARGE = ImageFont.truetype(font_path, 80)


def font_height(font, string=None):
    if string is not None:
        l, t, r, b = font.getbbox(string)
    l, t, r, b = font.getbbox(ascii_letters)
    return b - t


def font_str_width(font, string):
    l, t, r, b = font.getbbox(string)
    return r - l


def wrap_long_string(long_text, max_width, font):
    lines = []
    current_line = []
    words = long_text.split(' ')

    for word in words:
        test_line = ' '.join(current_line + [word])

        if font_str_width(font, test_line) <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))  # Add the last line
    return "\n".join(lines)


def draw_string(image, font, string, pos, padding_x=0, align: Literal["left", "center", "right"] = "left"):
    wrapped = wrap_long_string(string, image.width - padding_x * 2, font)

    spare_space = image.width - font_str_width(font, wrapped) - padding_x * 2

    x = pos[0] + padding_x
    if align == "center" and spare_space > 0:
        # the width estimation of a string with emojis in it will be wrong.
        x += int(spare_space / 2)
    elif align == "right" and spare_space > 0:
        x += spare_space

    draw = ImageDraw.Draw(image)
    # draw.text((pos[0] + padding_x, pos[1]), wrapped, font=font)
    with Pilmoji(image) as pilmoji:
        pilmoji.text((x, pos[1]), wrapped, font=font)


class TaskType(str, Enum):
    IDEA = "Idea"
    URGENT = "Urgent"
    TODO = "Todo"
    ARCHIVE = "Archive"


def print_task(task, task_type: TaskType):
    emoji = {
        TaskType.IDEA: "‼️",
        TaskType.URGENT: "🧨",
        TaskType.TODO: "📋",
        TaskType.ARCHIVE: "💾"
    }[task_type]

    im = Image.new("L", (512, 128*2), "#ffffff")

    # draw_string(im, FONT_LARGE, emoji, (0, 30), MAX_WIDTH,
    #             padding_x=50, align="right")
    # draw_string(im, FONT_LARGE, emoji, (0, 30), MAX_WIDTH,
    #             padding_x=50, align="right")
    draw_string(im, FONT_LARGE, emoji, (0, 0),
                padding_x=30, align="left")
    draw_string(im, FONT, task, (0, font_height(FONT_LARGE)),
                padding_x=30, align="center")
    return im
    # im.show()


def print_text(text):
    # im = Image.new("L", (512, 256), "#ffffff")
    # draw_string(im, FONT, text, (0, 104), MAX_WIDTH)
    text_height = ceil(font_height(
        FONT, string=wrap_long_string(text, MAX_WIDTH, FONT)))
    im = Image.new("L", (MAX_WIDTH, text_height), "#ffffff")
    draw_string(im, FONT, text, (0, 0), MAX_WIDTH)
    return im


if __name__ == "__main__":
    im = print_task("Thomas var her", TaskType.ARCHIVE)
    im.show()

# im = Image.new("L", (512, 512), "#ffffff")
# s = "The quick brown fox jumps over the lazy dog"
# draw_string(im, s * 100, (0, 15), MAX_WIDTH, 15)

# im.show()
