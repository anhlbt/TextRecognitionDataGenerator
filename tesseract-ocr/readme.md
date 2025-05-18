## run jTessBoxEditor
java -Xms128m -Xmx1024m -jar jTessBoxEditor.jar

## run docker image
```bash
docker run --rm -it \
  -v "$(pwd)/data:/tesseract/tesstrain/data" \
  -v /usr/share/fonts:/usr/share/fonts:ro \
  tesseract-ocr-tesseract /bin/bash
```