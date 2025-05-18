import cv2

def draw_boxes(image_path: str, box_file_path: str, output_path: str, show_whitespace: bool = True):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")
    height = image.shape[0]

    def parse_box_line(line: str):
        line = line.rstrip("\n")
        space_idx = line.find(" ")
        if space_idx == -1:
            return None
        char = line[:space_idx]
        rest = line[space_idx + 1:].split()
        if len(rest) != 5:
            return None
        x1, y1, x2, y2 = map(int, rest[:4])
        return char, x1, y1, x2, y2

    with open(box_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        parsed = parse_box_line(line)
        if parsed is None:
            continue
        char, x1, y1, x2, y2 = parsed

        # Tesseract gốc ảnh là bottom-left
        y1_img = height - y1
        y2_img = height - y2

        # Vẽ box
        cv2.rectangle(image, (x1, y2_img), (x2, y1_img), (0, 255, 0), 1)

        # if char == ' ':
        #     if show_whitespace:
        #         cv2.putText(image, '␣', (x1, y1_img - 5),
        #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        # else:
        #     cv2.putText(image, char, (x1, y1_img - 5),
        #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.imwrite(output_path, image)
    print(f"✅ Đã lưu ảnh với bounding boxes vào: {output_path}")



if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = "/media/anhlbt/SSD2/workspace/TextRecognitionDataGenerator/trdg/out/dataset/0.jpg"  # Đường dẫn tới ảnh gốc
    box_file_path = "/media/anhlbt/SSD2/workspace/TextRecognitionDataGenerator/trdg/out/dataset/0.box"  # Đường dẫn tới file .box
    output_path = "image_with_boxes.png"  # Đường dẫn lưu ảnh đã annotate

    draw_boxes(image_path, box_file_path, output_path)