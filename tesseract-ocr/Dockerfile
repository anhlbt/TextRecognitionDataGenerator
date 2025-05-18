# Sử dụng hình ảnh Ubuntu làm base
FROM ubuntu:20.04

# Thiết lập biến môi trường để tránh tương tác trong quá trình cài đặt
ENV DEBIAN_FRONTEND=noninteractive

# Cập nhật và cài đặt các gói cần thiết
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    nano \
    build-essential \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    zlib1g-dev \
    libicu-dev \
    libpango1.0-dev \
    libcairo2-dev \
    libfontconfig1-dev \
    automake \
    autotools-dev \
    libtool \
    pkg-config \
    python3 \
    python3-pip \
    lsb-release \
    ttf-mscorefonts-installer \
    fonts-wqy-zenhei \
    imagemagick \
    && fc-cache -f -v \
    && apt-get clean

# Cài đặt Leptonica từ GitHub release
RUN wget https://github.com/DanBloomberg/leptonica/releases/download/1.82.0/leptonica-1.82.0.tar.gz \
    && tar -zxvf leptonica-1.82.0.tar.gz \
    && cd leptonica-1.82.0 \
    && ./configure \
    && make \
    && make install \
    && cd .. \
    && rm -rf leptonica-1.82.0 leptonica-1.82.0.tar.gz

# Cài đặt Tesseract 5 từ source
RUN git clone https://github.com/tesseract-ocr/tesseract.git \
    && cd tesseract \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
    && make training \
    && make training-install \
    && cd .. \
    && rm -rf tesseract

# Cài đặt công cụ tesstrain
RUN git clone https://github.com/tesseract-ocr/tesstrain.git /tesseract/tesstrain

# Cài đặt các phụ thuộc Python
WORKDIR /tesseract/tesstrain
RUN pip3 install --no-cache-dir lxml pillow
RUN pip install -r requirements.txt

# Thiết lập biến môi trường
ENV TESSDATA_PREFIX=/usr/local/share/tessdata
ENV TESSERACT_OEM=1

# Tạo các thư mục cần thiết
RUN mkdir -p /tesseract/tesstrain/data \
    && mkdir -p /usr/local/share/tessdata

# Tải file .traineddata
RUN wget -P /usr/local/share/tessdata https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata \
    && wget -P /usr/local/share/tessdata https://github.com/tesseract-ocr/tessdata_best/raw/main/vie.traineddata \
    && wget -P /usr/local/share/tessdata https://github.com/tesseract-ocr/tessdata_best/raw/main/chi_tra.traineddata

# Sao chép langdata
RUN make tesseract-langdata

# Cài đặt font bổ sung
RUN apt-get update && apt-get install -y \
    ttf-mscorefonts-installer \
    fonts-wqy-zenhei \
    fonts-noto-cjk-extra \
    fonts-noto-cjk \
    parallel \
    && fc-cache -f -v

RUN apt-get update && apt-get install -y fonts-noto* && rm -rf /var/lib/apt/lists/*
# Cài pip packages
# Cài các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 libpng-dev \
    libgl1 \
    tesseract-ocr \
    fonts-dejavu \
    bc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    opencv-python-headless \
    imgaug \
    fonttools \
    numpy \
    pillow \
    trdg \
    tensorflow


    # Sao chép train.sh, convert2lstm.py và generate_data.py vào container
COPY train.sh /tesseract/tesstrain/train.sh
COPY generate_data.py /tesseract/tesstrain/generate_data.py
COPY gen_box_and_lstmf.sh /tesseract/tesstrain/gen_box_and_lstmf.sh
COPY ocr_evaluate.py /tesseract/tesstrain/ocr_evaluate.py
RUN chmod +x /tesseract/tesstrain/train.sh
RUN chmod +x /tesseract/tesstrain/gen_box_and_lstmf.sh
# Cấp quyền cho thư mục
RUN chmod -R 777 /tesseract/tesstrain/

# Thiết lập thư mục làm việc
WORKDIR /tesseract/tesstrain
