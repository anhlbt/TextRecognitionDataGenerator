import os
import pytesseract
from PIL import Image
from difflib import SequenceMatcher

GT_DIR = "./tesstrain/data/multi_lang-ground-truth"

def load_gt_text(gt_file):
    with open(gt_file, encoding="utf-8") as f:
        return f.read().strip()

def evaluate_ocr(image_path, gt_text):
    ocr_text = pytesseract.image_to_string(Image.open(image_path), lang='eng+vie', config='--psm 7')
    ratio = SequenceMatcher(None, gt_text, ocr_text.strip()).ratio()
    return ocr_text.strip(), ratio

def main():
    total_score = 0
    count = 0
    for file in os.listdir(GT_DIR):
        if file.endswith(".tif"):
            img_path = os.path.join(GT_DIR, file)
            gt_path = img_path.replace(".tif", ".gt.txt")
            gt_text = load_gt_text(gt_path)
            ocr_text, score = evaluate_ocr(img_path, gt_text)
            print(f"[{file}] GT: '{gt_text}' | OCR: '{ocr_text}' | Accuracy: {score:.2f}")
            total_score += score
            count += 1

    if count > 0:
        print(f"\n🎯 Average OCR Accuracy: {total_score / count:.2%}")

if __name__ == "__main__":
    main()
