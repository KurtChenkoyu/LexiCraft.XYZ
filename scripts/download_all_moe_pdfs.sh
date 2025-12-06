#!/bin/bash
# Download all Taiwan MOE word list PDFs

echo "Downloading Taiwan MOE word list PDFs..."
echo ""

# Create downloads directory
mkdir -p downloads
cd downloads

# GEPT Elementary
echo "Downloading GEPT Elementary..."
curl -L -o GEPT_Elementary.pdf "https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_Elementary.pdf"

# GEPT Intermediate
echo "Downloading GEPT Intermediate..."
curl -L -o GEPT_Intermediate.pdf "https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_Intermediate.pdf"

# GEPT High-Intermediate
echo "Downloading GEPT High-Intermediate..."
curl -L -o GEPT_High-Intermediate.pdf "https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf"

# SHERWL (Senior High School English Reference Word List)
echo "Downloading SHERWL..."
curl -L -o "SHERWL_高中英文參考詞彙表.pdf" "https://www.ceec.edu.tw/files/file_pool/1/0k213571061045122620/%e9%ab%98%e4%b8%ad%e8%8b%b1%e6%96%87%e5%8f%83%e8%80%83%e8%a9%9e%e5%bd%99%e8%a1%a8%28111%e5%ad%b8%e5%b9%b4%e5%ba%a6%e8%b5%b7%e9%81%a9%e7%94%a8%29.pdf"

echo ""
echo "✅ All PDFs downloaded to downloads/ directory"
echo ""
echo "Next step: Run the extraction script:"
echo "  python3 scripts/extract_moe_from_pdf.py downloads/*.pdf"

