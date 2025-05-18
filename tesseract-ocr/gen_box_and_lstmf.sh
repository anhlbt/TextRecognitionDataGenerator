#!/bin/bash

# Đường dẫn tới thư mục chứa ảnh .jpg
IMG_PATH="/tesseract/tesstrain/data/multi_lang-ground-truth"

# Hàm xử lý từng file ảnh
process_image() {
    IMG_FILE="$1"
    BASE_NAME=$(basename "$IMG_FILE" .jpg)
    echo "📦 Generating .lstmf for $IMG_FILE"

    # Tạo file .lstmf dùng để train
    tesseract "$IMG_FILE" "$IMG_PATH/$BASE_NAME" --psm 13 lstm.train

    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate .lstmf for $IMG_FILE"
        return 1
    fi

    echo "✅ Successfully generated .box and .lstmf for $IMG_FILE"
}

export -f process_image
export IMG_PATH

# Kiểm tra xem có file .jpg nào không
if ! ls "$IMG_PATH"/*.jpg >/dev/null 2>&1; then
    echo "❌ No .jpg files found in $IMG_PATH"
    exit 1
fi

# Chạy song song với parallel, giới hạn số lượng job (ví dụ: 4 job đồng thời)
find "$IMG_PATH" -type f -name "*.jpg" | parallel -j16 process_image {}

echo "🎉 All .lstmf files generated!"