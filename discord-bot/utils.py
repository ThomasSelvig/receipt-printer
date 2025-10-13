from enum import Enum
from typing import Literal
from PIL import Image, ImageFont, ImageDraw
from pilmoji.core import Pilmoji


MAX_WIDTH = 512
# font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font_path = "OpenSans-VariableFont_wdth,wght.ttf"
FONT = ImageFont.truetype(font_path, 24)
FONT_LARGE = ImageFont.truetype(font_path, 64)


def wrap_long_string(long_text, max_width, font):
    lines = []
    current_line = []
    words = long_text.split(' ')

    for word in words:
        test_line = ' '.join(current_line + [word])
        # Use font.getbbox() to get precise text size for Pillow 9+
        # For older versions, font.getsize() might be used
        l, t, r, b = font.getbbox(test_line)
        text_width = r - l

        if text_width <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))  # Add the last line
    return "\n".join(lines)


def draw_string(image, font, string, pos, max_width, padding_x=0, align: Literal["left", "center", "right"] = "left"):
    wrapped = wrap_long_string(string, max_width - padding_x * 2, font)

    text_width = font.getbbox(wrapped)[2] - font.getbbox(wrapped)[0]
    spare_space = max_width - text_width - padding_x * 2

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
        "idea": "💡",
        "urgent": "🔔",
        "todo": "📋",
        "archive": "💾"
    }[task_type]

    im = Image.new("L", (512, 128*2), "#ffffff")

    # draw_string(im, FONT_LARGE, emoji, (0, 30), MAX_WIDTH,
    #             padding_x=50, align="right")
    # draw_string(im, FONT_LARGE, emoji, (0, 30), MAX_WIDTH,
    #             padding_x=50, align="right")
    draw_string(im, FONT_LARGE, emoji * 1, (0, 30), MAX_WIDTH,
                padding_x=30, align="left")
    draw_string(im, FONT, task, (0, 104), MAX_WIDTH,
                padding_x=30, align="center")
    return im
    # im.show()


def print_text(text):
    im = Image.new("L", (512, 256), "#ffffff")
    draw_string(im, FONT, text, (0, 104), MAX_WIDTH)
    return im


if __name__ == "__main__":
    # removed im.show(), add back for debug
    print_task("Thomas var her", TaskType.ARCHIVE)
# im = Image.new("L", (512, 512), "#ffffff")
# s = "The quick brown fox jumps over the lazy dog"
# draw_string(im, s * 100, (0, 15), MAX_WIDTH, 15)

# im.show()
