import os
import random
import json
import subprocess
import numpy as np
from PIL import Image
from fontTools.ttLib import TTFont


from os.path import dirname, realpath, join
import sys
C_DIR = dirname(realpath(__file__))
P_DIR = dirname(C_DIR)
sys.path.insert(0, P_DIR)

from trdg.generators import GeneratorFromStrings

# === CẤU HÌNH ===
NUM_IMAGES = 1000
LANGS = ["eng", "vie"]
FONT_DIR = "/usr/share/fonts/truetype"
SAVE_DIR = "./data/multi_lang-ground-truth"
CACHE_FILE = os.path.join(SAVE_DIR, "font_cache.json")
DICT_FILES = {
    "eng": "data/dict/english_words.txt",
    "vie": "data/dict/vietnamese_words.txt"
}
FONTSIZE = 40
IMAGE_WIDTH = 800

os.makedirs(SAVE_DIR, exist_ok=True)

# === FONT SUPPORT ===
def check_language_support(font_path, text):
    try:
        font = TTFont(font_path)
        cmap = None
        for table in font['cmap'].tables:
            if table.platformID == 3 and table.platEncID == 10:
                cmap = table.cmap
                break
        if cmap is None:
            for table in font['cmap'].tables:
                if table.platformID == 0 and table.platEncID == 3:
                    cmap = table.cmap
                    break
        if cmap:
            for char in text:
                if ord(char) not in cmap:
                    return False
            return True
        return False
    except:
        return False

def check_font_support(text, font_path):
    return check_language_support(font_path, text)

# === TỪ ĐIỂN ===
def load_dictionary(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
        valid = lambda c: c.isalnum() or c.isspace() or c in "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ"
        return [w for w in words if all(valid(c) for c in w)]
    except:
        return []

def get_unique_chars_from_dictionary(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return ''.join(set(text) - {'\n', '\r'})
    except:
        return ""

def generate_sentence(dictionary, length=7):
    if not dictionary:
        return "default text"
    sentence = " ".join(random.choices(dictionary, k=length))
    return sentence

# === FONT CACHE ===
def get_available_fonts():
    try:
        result = subprocess.run(["fc-list", "--format=%{file}\n"], capture_output=True, text=True, check=True)
        font_paths = result.stdout.strip().split("\n")
        return [path for path in font_paths if path.endswith((".ttf", ".ttc"))]
    except Exception as e:
        print(f"Lỗi khi lấy danh sách font: {e}")
        return []

def select_fonts_for_language(lang, font_paths, dict_path):
    text = get_unique_chars_from_dictionary(dict_path)
    if not text:
        text = "Hello World 123" if lang == "eng" else "Xin chào thế giới áàảãạ"
    return [f for f in font_paths if check_font_support(text, f)] or ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]

def load_font_cache(dict_files):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            valid_cache = {}
            for lang, fonts in cache.items():
                dict_path = dict_files[lang]
                text = get_unique_chars_from_dictionary(dict_path)
                valid_fonts = [f for f in fonts if check_font_support(text, f)]
                if valid_fonts:
                    valid_cache[lang] = valid_fonts
            if valid_cache:
                return valid_cache
        except:
            pass
    return None

def save_font_cache(fonts):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(fonts, f, ensure_ascii=False, indent=2)
    except:
        pass

# === RENDER BẰNG TRDG ===
def generate_image_with_trdg(text, font_path, output_image_path, output_box_path, gt_path):
    print(f"text: {text}")
    if not text.strip():
        return False

    generator = GeneratorFromStrings(
        strings=[text],
        fonts=[font_path],
        size=FONTSIZE,
        output_mask=True
    )

    for img, lbl, box_coords in generator:
        img.save(output_image_path)

        with open(gt_path, "w", encoding="utf-8") as f:
            f.write(text)

        with open(output_box_path, "w", encoding="utf-8") as f:
            for char, (x1, y1, x2, y2) in zip(lbl, box_coords):
                f.write(f"{char} {x1} {img.height - y2} {x2} {img.height - y1} 0\n")

        return True
    return False

# === TẠO .lstmf bằng tesseract ===
def generate_training_files(img_path, lang_code):
    base_name = os.path.splitext(img_path)[0]
    try:
        print(f"📦 Generating .lstmf for {img_path}")
        subprocess.run([
            "tesseract", img_path, base_name, "-l", lang_code,
            "--psm", "6", "lstm.train"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during .lstmf generation for {img_path}: {e}")

# === MAIN ===
def main(refresh_cache=True):
    FONTS = load_font_cache(DICT_FILES)
    if FONTS is None or refresh_cache:
        all_fonts = get_available_fonts()
        if not all_fonts:
            print("No fonts found, exiting")
            return
        FONTS = {
            "eng": select_fonts_for_language("eng", all_fonts, DICT_FILES["eng"]),
            "vie": select_fonts_for_language("vie", all_fonts, DICT_FILES["vie"])
        }
        save_font_cache(FONTS)

    for lang in LANGS:
        words = load_dictionary(DICT_FILES[lang])
        if not words:
            print(f"No words loaded for {lang}, skipping")
            continue
        for i in range(NUM_IMAGES // len(LANGS)):
            sentence = generate_sentence(words)
            font_path = random.choice(FONTS[lang])
            base_name = f"{lang}_{i:04d}"
            img_path = os.path.join(SAVE_DIR, base_name + ".tif")
            gt_path = os.path.join(SAVE_DIR, base_name + ".gt.txt")
            box_path = os.path.join(SAVE_DIR, base_name + ".box")

            success = generate_image_with_trdg(sentence, font_path, img_path, box_path, gt_path)
            if success:
                print(f"✅ Created {img_path}")
                generate_training_files(img_path, lang)
            else:
                print(f"❌ Failed to create {img_path}")

if __name__ == "__main__":
    main(refresh_cache=True)
