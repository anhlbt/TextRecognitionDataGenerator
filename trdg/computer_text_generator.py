import random as rnd
from typing import Tuple
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from trdg.utils import get_text_width, get_text_height

# Thai Unicode reference: https://jrgraphix.net/r/Unicode/0E00-0E7F
TH_TONE_MARKS = [
    "0xe47",
    "0xe48",
    "0xe49",
    "0xe4a",
    "0xe4b",
    "0xe4c",
    "0xe4d",
    "0xe4e",
]
TH_UNDER_VOWELS = ["0xe38", "0xe39", "\0xe3A"]
TH_UPPER_VOWELS = ["0xe31", "0xe34", "0xe35", "0xe36", "0xe37"]


def generate(
    is_draw_bounding_box: bool,
    text: str,
    font: str,
    text_color: str,
    font_size: int,
    orientation: int,
    space_width: int,
    character_spacing: int,
    fit: bool,
    word_split: bool,
    stroke_width: int = 0,
    stroke_fill: str = "#282828",
) -> Tuple:
    if orientation == 0:
        return _generate_horizontal_text(is_draw_bounding_box,
            text,
            font,
            text_color,
            font_size,
            space_width,
            character_spacing,
            fit,
            word_split,
            stroke_width,
            stroke_fill,
        )
    elif orientation == 1:
        return _generate_vertical_text(
            text,
            font,
            text_color,
            font_size,
            space_width,
            character_spacing,
            fit,
            stroke_width,
            stroke_fill,
        )
    else:
        raise ValueError("Unknown orientation " + str(orientation))


def _compute_character_width(image_font: ImageFont, character: str) -> int:
    if len(character) == 1 and (
        "{0:#x}".format(ord(character))
        in TH_TONE_MARKS + TH_UNDER_VOWELS + TH_UNDER_VOWELS + TH_UPPER_VOWELS
    ):
        return 0
    # Casting as int to preserve the old behavior
    return round(image_font.getlength(character))



def _generate_horizontal_text(
    is_draw_bounding_box,
    text,
    font,
    text_color,
    font_size,
    space_width,
    character_spacing,
    fit,
    word_split,
    stroke_width=0,
    stroke_fill="#282828",
    bounding_box_color="#000000"
):
    """
    Generate an image with horizontal text, optionally drawing bounding boxes around characters.
    
    Args:
        is_draw_bounding_box (bool): Whether to draw bounding boxes around characters.
        text (str): The text to render.
        font (str): Path to the font file.
        text_color (str): Color(s) for the text (e.g., "#FFFFFF" or "red,blue" for gradient).
        font_size (int): Font size in points.
        space_width (float): Multiplier for space width.
        character_spacing (int): Spacing between characters (when word_split=False).
        fit (bool): Whether to crop the image to fit the text.
        word_split (bool): Whether to split text into words.
        stroke_width (int): Width of text stroke.
        stroke_fill (str): Color(s) for text stroke.
        bounding_box_color (str): Color for bounding box outline.
    
    Returns:
        tuple: (text_image, text_mask) - PIL Image objects for the text and mask.
    """
    image_font = ImageFont.truetype(font=font, size=font_size)
    
    # Calculate space width
    try:
        space_width = int(image_font.getlength(" ") * space_width)
    except Exception as ex:
        print(f"Error calculating space width for font {font}: {ex}")
        space_width = 1

    # Split text if word_split is enabled
    if word_split:
        splitted_text = []
        for w in text.split(" "):
            splitted_text.append(w)
            splitted_text.append(" ")
        splitted_text.pop()  # Remove trailing space
    else:
        splitted_text = list(text)  # Treat each character individually

    # Cache for character widths and bounding boxes
    char_cache = {}

    def _compute_character_info(p):
        if p in char_cache:
            return char_cache[p]
        width = image_font.getlength(p) if p != " " else space_width
        bbox = image_font.getbbox(p)
        char_cache[p] = (width, bbox)
        return width, bbox

    # Compute widths and heights
    piece_info = [_compute_character_info(p) for p in splitted_text]
    piece_widths = [info[0] for info in piece_info]
    text_width = sum(piece_widths)
    if not word_split:
        text_width += character_spacing * (len(text) - 1)

    text_height = max([get_text_height(image_font, p) for p in splitted_text])
    # Create images
    txt_img = Image.new("RGBA", (int(text_width), int(text_height)), (0, 0, 0, 0))
    txt_mask = Image.new("RGB", (int(text_width), int(text_height)), (0, 0, 0))
    txt_img_draw = ImageDraw.Draw(txt_img)
    txt_mask_draw = ImageDraw.Draw(txt_mask, mode="RGB")
    txt_mask_draw.fontmode = "1"

    # Prepare colors
    colors = [ImageColor.getrgb(c) for c in text_color.split(",")]
    c1, c2 = colors[0], colors[-1]
    fill = (
        rnd.randint(min(c1[0], c2[0]), max(c1[0], c2[0])),
        rnd.randint(min(c1[1], c2[1]), max(c1[1], c2[1])),
        rnd.randint(min(c1[2], c2[2]), max(c1[2], c2[2])),
        rnd.randint(50, 255)  # alpha
    )

    stroke_colors = [ImageColor.getrgb(c) for c in stroke_fill.split(",")]
    stroke_c1, stroke_c2 = stroke_colors[0], stroke_colors[-1]
    stroke_fill = (
        rnd.randint(min(stroke_c1[0], stroke_c2[0]), max(stroke_c1[0], stroke_c2[0])),
        rnd.randint(min(stroke_c1[1], stroke_c2[1]), max(stroke_c1[1], stroke_c2[1])),
        rnd.randint(min(stroke_c1[2], stroke_c2[2]), max(stroke_c1[2], stroke_c2[2])),
    )

    # Draw text and bounding boxes
    for i, p in enumerate(splitted_text):
        x_pos = sum(piece_widths[0:i]) + i * character_spacing * int(not word_split)
        
        # Draw text
        try:
            txt_img_draw.text(
                (x_pos, 0),
                p,
                fill=fill,
                font=image_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
        except Exception as ex:
            print(f"Error drawing text '{p}' with font {font}: {ex}")
            continue

        # Draw bounding box
        if is_draw_bounding_box and p != " ":
            width, bbox = piece_info[i]
            if bbox is None:
                continue  # Skip invalid characters
            left_bbox, top, right_bbox, bottom = bbox
            
            # Calculate bounding box coordinates
            right = x_pos + width
            left = x_pos
            
            # Ensure valid top and bottom with minimal padding
            padding = 2  # Reduced padding to avoid issues with small characters
            top = max(0, top - padding)
            bottom = min(text_height, bottom + padding)
            
            # Skip if top >= bottom (invalid rectangle)
            if top >= bottom:
                print(f"Skipping bounding box for '{p}' with font {font}: Invalid coordinates (top={top}, bottom={bottom})")
                continue

            try:
                txt_img_draw.rectangle(
                    (left, top, right, bottom),
                    outline=bounding_box_color,
                    fill=None
                )
            except Exception as ex:
                print(f"Error drawing bounding box for '{p}' with font {font}: {ex}")

        # Draw mask
        try:
            txt_mask_draw.text(
                (x_pos, 0),
                p,
                fill=((i + 1) // (255 * 255), (i + 1) // 255, (i + 1) % 255),
                font=image_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
        except Exception as ex:
            print(f"Error drawing mask for '{p}' with font {font}: {ex}")

    # Crop if fit is enabled
    if fit:
        text_bbox = txt_img.getbbox()
        if text_bbox:
            return txt_img.crop(text_bbox), txt_mask.crop(text_bbox)
    
    return txt_img, txt_mask


def _generate_vertical_text(
    text: str,
    font: str,
    text_color: str,
    font_size: int,
    space_width: int,
    character_spacing: int,
    fit: bool,
    stroke_width: int = 0,
    stroke_fill: str = "#282828",
) -> Tuple:
    image_font = ImageFont.truetype(font=font, size=font_size)

    space_height = int(get_text_height(image_font, " ") * space_width)

    char_heights = [
        get_text_height(image_font, c) if c != " " else space_height for c in text
    ]
    text_width = max([get_text_width(image_font, c) for c in text])
    text_height = sum(char_heights) + character_spacing * len(text)

    txt_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    txt_mask = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))

    txt_img_draw = ImageDraw.Draw(txt_img)
    txt_mask_draw = ImageDraw.Draw(txt_mask)
    txt_mask_draw.fontmode = "1"

    colors = [ImageColor.getrgb(c) for c in text_color.split(",")]
    c1, c2 = colors[0], colors[-1]

    fill = (
        rnd.randint(c1[0], c2[0]),
        rnd.randint(c1[1], c2[1]),
        rnd.randint(c1[2], c2[2]),
    )

    stroke_colors = [ImageColor.getrgb(c) for c in stroke_fill.split(",")]
    stroke_c1, stroke_c2 = stroke_colors[0], stroke_colors[-1]

    stroke_fill = (
        rnd.randint(stroke_c1[0], stroke_c2[0]),
        rnd.randint(stroke_c1[1], stroke_c2[1]),
        rnd.randint(stroke_c1[2], stroke_c2[2]),
    )

    for i, c in enumerate(text):
        txt_img_draw.text(
            (0, sum(char_heights[0:i]) + i * character_spacing),
            c,
            fill=fill,
            font=image_font,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        txt_mask_draw.text(
            (0, sum(char_heights[0:i]) + i * character_spacing),
            c,
            fill=((i + 1) // (255 * 255), (i + 1) // 255, (i + 1) % 255),
            font=image_font,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

    if fit:
        return txt_img.crop(txt_img.getbbox()), txt_mask.crop(txt_img.getbbox())
    else:
        return txt_img, txt_mask