###copy fonts
for file in ./*/*.ttf; do cp $file /home/anhlbt/source/workspace/nlp/TextRecognitionDataGenerator/trdg/fonts/go; done

The only remaining blacklisted families with this issue are:
Padauk
KumarOne


### generate dataset
WordStr <left> <bottom> <right> <top> <page> #<text>

#number
python run.py -c 1000 -w 4 -r -f 64 -rs -num --output_dir $(pwd)/out_color/ --font_dir fonts/go/ --image_dir images/ --thread_count 16 -na 2 -k 10 -rk -bl 1 -rbl -cs 10

#text
python run.py -c 1000 -w 4 -r -f 64 -rs -i $(pwd)/texts/random_3.txt --output_dir $(pwd)/out/ --font_dir fonts/go/ --image_dir images/ --thread_count 16 -na 2 -k 2 -bl 1 -rbl -obb 2 -dbb 20



# Tạo dữ liệu huấn luyện với TextRecognitionDataGenerator (trdg)
python run.py \
  -c 10000 \
  -w 4 \
  -r \
  -f 64 \
  -rs \
  -i "$(pwd)/texts/random_3.txt" \
  --output_dir "/media/anhlbt/SSD2/workspace/TextRecognitionDataGenerator/tesseract-ocr/data/multi_lang-ground-truth" \
  --font_dir "fonts/go/" \
  --image_dir "images/" \
  --thread_count 16 \
  -na 2 \
  -k 2 \
  -bl 1 \
  -rbl \
  -obb 2 \
  -dbb 20 



python run.py -c 1000 -w 5 -f 64


out_dir=~/dataset/digit_up_letters
python run.py -c 100000 -w 4 -r -f 64 -rs -num --output_dir ~/dataset/digit_up_letters --font_dir fonts/go/ --image_dir images/ --thread_count 16 -na  -k 10 -rk -bl 1 -rbl -cs 10



scp -r ~/dataset/digit_gen hoscv01@10.166.2.106:/media/ocr_dataset/digit_gen
