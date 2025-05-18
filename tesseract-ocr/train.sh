#!/bin/bash
# Script huấn luyện mô hình OCR đa ngôn ngữ (Anh, Việt, Trung) với Tesseract 5.x trong Docker, có Early Stopping

set -e

echo "📁 Thư mục làm việc: $(pwd)"

# --- Kiểm tra phiên bản Tesseract ---
TESSERACT_VERSION=$(tesseract --version | head -n1 | cut -d' ' -f2)
if [[ ! $TESSERACT_VERSION =~ ^5\..* ]]; then
    echo "❌ Lỗi: Yêu cầu Tesseract 5.x. Phiên bản hiện tại: $TESSERACT_VERSION"
    exit 1
fi

# --- Biến cấu hình ---
export TESSDATA_PREFIX=/usr/local/share/tessdata
export TESSERACT_OEM=1
MODEL_NAME="multi_lang"
GROUND_TRUTH_DIR="/tesseract/tesstrain/data/multi_lang-ground-truth"
DATA_DIR="/tesseract/tesstrain/data"
MODEL_DIR="${DATA_DIR}/${MODEL_NAME}"
LSTM_TRAIN_FILE="/tesseract/tesstrain/lstm.train"
MAX_ITERATIONS=200000
LEARNING_RATE=0.001  # Tăng từ 0.0001 để cải thiện tốc độ học
STOP_THRESHOLD=0.001

mkdir -p "${GROUND_TRUTH_DIR}" "${MODEL_DIR}"

# --- Tạo lstm.train nếu chưa có ---
if [ ! -f "${LSTM_TRAIN_FILE}" ]; then
    echo -e "load_system_dawg 0\nload_freq_dawg 0" > "${LSTM_TRAIN_FILE}"
    chmod u+r "${LSTM_TRAIN_FILE}"
else
    grep -q "load_system_dawg 0" "${LSTM_TRAIN_FILE}" || echo "load_system_dawg 0" >> "${LSTM_TRAIN_FILE}"
    grep -q "load_freq_dawg 0" "${LSTM_TRAIN_FILE}" || echo "load_freq_dawg 0" >> "${LSTM_TRAIN_FILE}"
fi

echo "📄 Nội dung lstm.train:"
cat "${LSTM_TRAIN_FILE}"

# --- Kiểm tra traineddata gốc ---
for lang in eng vie; do
    traineddata_file="${TESSDATA_PREFIX}/${lang}.traineddata"
    if [ ! -f "${traineddata_file}" ]; then
        echo "❌ Lỗi: Không tìm thấy ${traineddata_file}"
        exit 1
    fi
done

# --- Sửa Makefile nếu cần (cho Tesseract 5.4 trở lên) ---
MAKEFILE="/tesseract/tesstrain/Makefile"
if grep -q "tesseract.*--psm 13 lstm.train" "${MAKEFILE}"; then
    sed -i 's/--psm 13 lstm.train/--psm 13 --oem 1/' "${MAKEFILE}"
fi

# --- Phân tích ký tự ---
echo "🔠 Phân tích ký tự..."
cat "${GROUND_TRUTH_DIR}"/*.gt.txt | grep -o . | sort | uniq -c | sort -nr > "${DATA_DIR}/char_distribution.txt"
echo "✅ Lưu tại: ${DATA_DIR}/char_distribution.txt"

# --- Tạo unicharset ---
echo "🔤 Tạo unicharset..."
unicharset_extractor --norm_mode 2 --output_unicharset "${MODEL_DIR}/unicharset" "${GROUND_TRUTH_DIR}"/*.gt.txt 2> "${DATA_DIR}/unicharset_error.log" || {
    echo "❌ Lỗi tạo unicharset:"
    cat "${DATA_DIR}/unicharset_error.log"
    exit 1
}

UNICHARSET_SIZE=$(wc -l < "${MODEL_DIR}/unicharset")
echo "🔢 Số ký tự: ${UNICHARSET_SIZE}"

NET_SPEC="[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 O1c${UNICHARSET_SIZE}]"  # Đơn giản hóa mạng

# --- Kiểm tra và xử lý file .lstmf bị thiếu ---
echo "🔍 Kiểm tra file .lstmf..."
if ! ls "${GROUND_TRUTH_DIR}"/*.lstmf >/dev/null 2>&1; then
    echo "⚠️ Không tìm thấy file .lstmf nào trong ${GROUND_TRUTH_DIR}"
    echo "❌ Lỗi: Cần ít nhất một file .lstmf để huấn luyện"
    exit 1
fi

# Tạo thư mục để lưu các file lỗi
ERROR_DIR="${DATA_DIR}/error_files"
mkdir -p "${ERROR_DIR}"

# Tìm các file ảnh thiếu .lstmf
missing_files=()
skipped_files=()
for img in "${GROUND_TRUTH_DIR}"/*.{jpg,png,tif}; do
    if [ -f "$img" ]; then
        base=$(basename "$img" | sed 's/\.[^.]*$//')
        if [ ! -f "${GROUND_TRUTH_DIR}/${base}.lstmf" ]; then
            echo "❌ Thiếu ${base}.lstmf cho $img"
            missing_files+=("$img")
        fi
    fi
done

# Tạo lại các file .lstmf bị thiếu
if [ ${#missing_files[@]} -gt 0 ]; then
    echo "📸 Tạo các file .lstmf bị thiếu..."
    for img in "${missing_files[@]}"; do
        base=$(basename "$img" | sed 's/\.[^.]*$//')
        echo "📦 Tạo .lstmf cho $img"
        tesseract "$img" "${GROUND_TRUTH_DIR}/${base}" --psm 13 --oem 1 lstm.train 2> "${DATA_DIR}/${base}_lstmf_error.log"
        if [ $? -eq 0 ] && [ -f "${GROUND_TRUTH_DIR}/${base}.lstmf" ]; then
            echo "✅ Đã tạo ${base}.lstmf"
        else
            echo "⚠️ Không thể tạo ${base}.lstmf. Di chuyển file ảnh và liên quan ra thư mục lỗi."
            cat "${DATA_DIR}/${base}_lstmf_error.log"
            mv "$img" "${ERROR_DIR}/" 2>/dev/null
            mv "${GROUND_TRUTH_DIR}/${base}.gt.txt" "${ERROR_DIR}/" 2>/dev/null
            mv "${GROUND_TRUTH_DIR}/${base}.box" "${ERROR_DIR}/" 2>/dev/null
            skipped_files+=("$base")
        fi
    done
fi

# Báo cáo các file bị bỏ qua
if [ ${#skipped_files[@]} -gt 0 ]; then
    echo "⚠️ Các file sau đã bị bỏ qua do không thể tạo .lstmf (đã di chuyển vào ${ERROR_DIR}):"
    for skipped in "${skipped_files[@]}"; do
        echo "- ${skipped}.lstmf"
    done
    echo "📝 Tiếp tục huấn luyện với các file .lstmf hiện có..."
else
    echo "✅ Tất cả file .lstmf cần thiết đã sẵn sàng hoặc đã được tạo"
fi

# --- Huấn luyện ---
echo "🚀 Bắt đầu huấn luyện ${MODEL_NAME}..."
EARLY_STOP_LOG="${MODEL_DIR}/early_stop.log"
rm -f "${EARLY_STOP_LOG}"

# Kiểm tra checkpoint gần nhất
CHECKPOINT_FILE=$(ls -t "${MODEL_DIR}"/*.checkpoint 2>/dev/null | head -n1)
if [ -n "$CHECKPOINT_FILE" ]; then
    echo "🔄 Tiếp tục huấn luyện từ checkpoint: $CHECKPOINT_FILE"
    make training \
        MODEL_NAME="${MODEL_NAME}" \
        GROUND_TRUTH_DIR="${GROUND_TRUTH_DIR}" \
        TESSDATA_PREFIX="${TESSDATA_PREFIX}" \
        MAX_ITERATIONS="${MAX_ITERATIONS}" \
        LEARNING_RATE="${LEARNING_RATE}" \
        RATIO_TRAIN=0.80 \
        NET_SPEC="${NET_SPEC}" \
        START_MODEL="${MODEL_NAME}" \
        CHECKPOINT_FILE="${CHECKPOINT_FILE}" \
    | tee "${EARLY_STOP_LOG}"
else
    echo "🆕 Bắt đầu huấn luyện từ đầu (không tìm thấy checkpoint)"
    make training \
        MODEL_NAME="${MODEL_NAME}" \
        GROUND_TRUTH_DIR="${GROUND_TRUTH_DIR}" \
        TESSDATA_PREFIX="${TESSDATA_PREFIX}" \
        MAX_ITERATIONS="${MAX_ITERATIONS}" \
        LEARNING_RATE="${LEARNING_RATE}" \
        RATIO_TRAIN=0.80 \
        NET_SPEC="${NET_SPEC}" \
    | tee "${EARLY_STOP_LOG}"
fi

# --- Kiểm tra dừng sớm ---
if grep -q "delta=" "${EARLY_STOP_LOG}"; then
    min_delta=$(grep -o 'delta=[0-9.]*%' "${EARLY_STOP_LOG}" | sed 's/delta=//' | sed 's/%//' | sort -n | head -n1)
    echo "📉 Delta nhỏ nhất: ${min_delta}%"
    stop_threshold=$(echo "${STOP_THRESHOLD} * 100" | bc -l)
    if (( $(echo "$min_delta < $stop_threshold" | bc -l) )); then
        echo "🛑 Dừng sớm: delta < ${STOP_THRESHOLD}"
        exit 0
    fi
fi

# --- Copy traineddata ---
TRAINED_FILE="${MODEL_DIR}/${MODEL_NAME}.traineddata"
if [ -f "${TRAINED_FILE}" ]; then
    cp "${TRAINED_FILE}" "${TESSDATA_PREFIX}/" && \
    echo "✅ Huấn luyện hoàn tất! Đã copy ${MODEL_NAME}.traineddata vào ${TESSDATA_PREFIX}" || {
        echo "❌ Không thể copy traineddata"
        exit 1
    }
else
    echo "❌ Không tìm thấy traineddata. Huấn luyện có thể đã thất bại."
    exit 1
fi

# --- Dự đoán với test.png (nếu có) ---
TEST_IMAGE="${DATA_DIR}/test.png"
OUTPUT_FILE="${DATA_DIR}/output"
TRAINED_FILE="${MODEL_DIR}/${MODEL_NAME}.traineddata"
if [ -f "${TEST_IMAGE}" ]; then
    echo "🔎 Dự đoán từ ${TEST_IMAGE}..."
    # Kiểm tra file traineddata
    if [ ! -f "${TRAINED_FILE}" ] || [ $(stat -c%s "${TRAINED_FILE}") -lt 100000 ]; then
        echo "⚠️ File ${TRAINED_FILE} không tồn tại hoặc quá nhỏ. Thử tạo lại..."
        lstmtraining \
            --stop_training \
            --continue_from "${MODEL_DIR}/checkpoints/multi_lang_checkpoint" \
            --traineddata "${MODEL_DIR}/multi_lang.traineddata" \
            --model_output "${TRAINED_FILE}" \
            2> "${DATA_DIR}/lstmtraining_error.log"
        if [ $? -ne 0 ]; then
            echo "❌ Lỗi khi tạo lại traineddata:"
            cat "${DATA_DIR}/lstmtraining_error.log"
            exit 1
        fi
        cp "${TRAINED_FILE}" "${TESSDATA_PREFIX}/" || {
            echo "❌ Không thể copy traineddata"
            exit 1
        }
    fi
    # Chạy tesseract và ghi log lỗi
    tesseract "${TEST_IMAGE}" "${OUTPUT_FILE}" -l "${MODEL_NAME}" --psm 3 --oem 1 2> "${DATA_DIR}/tesseract_error.log"
    if [ $? -eq 0 ] && [ -f "${OUTPUT_FILE}.txt" ]; then
        echo "✅ Kết quả OCR:"
        cat "${OUTPUT_FILE}.txt"
    else
        echo "❌ Lỗi khi chạy tesseract trên ảnh test:"
        cat "${DATA_DIR}/tesseract_error.log"
        exit 1
    fi
else
    echo "⚠️ Không tìm thấy test.png để kiểm thử"
fi