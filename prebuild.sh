#!/bin/bash
# Create directory for PaddleOCR models
mkdir -p ~/.paddleocr/whl/det/en/
mkdir -p ~/.paddleocr/whl/rec/en/
mkdir -p ~/.paddleocr/whl/cls/

# Download model files directly
wget https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar -P ~/.paddleocr/whl/det/en/
wget https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_rec_infer.tar -P ~/.paddleocr/whl/rec/en/
wget https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar -P ~/.paddleocr/whl/cls/

# Extract the tar files
cd ~/.paddleocr/whl/det/en/ && tar -xf en_PP-OCRv3_det_infer.tar
cd ~/.paddleocr/whl/rec/en/ && tar -xf en_PP-OCRv3_rec_infer.tar
cd ~/.paddleocr/whl/cls/ && tar -xf ch_ppocr_mobile_v2.0_cls_infer.tar

# Set permissions
chmod -R 755 ~/.paddleocr
