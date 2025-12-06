# Complete Taiwan MOE Word List Extraction Guide

This guide shows you how to extract word lists from all available Taiwan MOE PDF sources.

## Available PDF Sources

### GEPT (General English Proficiency Test) - LTTC
1. **Elementary** (初級): https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_Elementary.pdf
   - ~1,000-2,000 words
   - Level: 1 (Elementary)

2. **Intermediate** (中級): https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_Intermediate.pdf
   - ~2,000 words
   - Level: 3 (Intermediate)

3. **High-Intermediate** (中高級): https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf
   - ~2,000 words
   - Level: 5 (High-Intermediate)

### SHERWL (Senior High School English Reference Word List) - CEEC
4. **SHERWL** (高中英文參考詞彙表): https://www.ceec.edu.tw/files/file_pool/1/0k213571061045122620/%e9%ab%98%e4%b8%ad%e8%8b%b1%e6%96%87%e5%8f%83%e8%80%83%e8%a9%9e%e5%bd%99%e8%a1%a8%28111%e5%ad%b8%e5%b9%b4%e5%ba%a6%e8%b5%b7%e9%81%a9%e7%94%a8%29.pdf
   - 6,480 words
   - Levels: 1-6 (1,080 words per level)

## Quick Start - All PDFs at Once

### Option 1: Use the Download Script

```bash
# Download all PDFs automatically
./scripts/download_all_moe_pdfs.sh

# Extract all word lists
python3 scripts/extract_moe_from_pdf.py downloads/*.pdf
```

### Option 2: Manual Download

```bash
# Create downloads directory
mkdir -p downloads
cd downloads

# Download GEPT PDFs
curl -L -o GEPT_Elementary.pdf "https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_Elementary.pdf"
curl -L -o GEPT_Intermediate.pdf "https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_Intermediate.pdf"
curl -L -o GEPT_High-Intermediate.pdf "https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf"

# Download SHERWL
curl -L -o SHERWL.pdf "https://www.ceec.edu.tw/files/file_pool/1/0k213571061045122620/%e9%ab%98%e4%b8%ad%e8%8b%b1%e6%96%87%e5%8f%83%e8%80%83%e8%a9%9e%e5%bd%99%e8%a1%a8%28111%e5%ad%b8%e5%b9%b4%e5%ba%a6%e8%b5%b7%e9%81%a9%e7%94%a8%29.pdf"

cd ..

# Extract all
python3 scripts/extract_moe_from_pdf.py downloads/*.pdf
```

## Step-by-Step Instructions

### Step 1: Install Required Library

```bash
pip install pdfplumber
```

Or install all options:
```bash
pip install -r scripts/requirements_pdf.txt
```

### Step 2: Download PDFs

You can download all PDFs using the script or manually. The download script handles all the URLs automatically.

### Step 3: Extract Word Lists

Process all PDFs together (recommended):

```bash
python3 scripts/extract_moe_from_pdf.py \
  downloads/GEPT_Elementary.pdf \
  downloads/GEPT_Intermediate.pdf \
  downloads/GEPT_High-Intermediate.pdf \
  downloads/SHERWL.pdf
```

Or process individually:

```bash
# GEPT Elementary
python3 scripts/extract_moe_from_pdf.py downloads/GEPT_Elementary.pdf

# GEPT Intermediate
python3 scripts/extract_moe_from_pdf.py downloads/GEPT_Intermediate.pdf

# GEPT High-Intermediate
python3 scripts/extract_moe_from_pdf.py downloads/GEPT_High-Intermediate.pdf

# SHERWL
python3 scripts/extract_moe_from_pdf.py downloads/SHERWL.pdf
```

### Step 4: Verify Output

Check the generated file:

```bash
head -20 data/source/moe_7000.csv
```

You should see:
```csv
word,moe_level
a,1
ability,1
able,1
...
```

## PDF Format Details

### GEPT Elementary Format
- **Columns**: 字彙, 同類, 中文, 同類, 規劃, 學術字彙
- **Level Indicator**: "知識" (knowledge) = Level 1
- **Word Column**: First column (字彙)

### GEPT Intermediate/High-Intermediate Format
- **Columns**: 字集, 词源, 中文, 注释, 统数, 甲卅字集
- **Level Indicators**: 
  - 中线/中級 = Level 3
  - 中高线/中高級 = Level 5
- **Word Column**: First column (字集)

### SHERWL Format
- **Structure**: 6 levels, 1,080 words each
- **Levels**: Numeric 1-6
- **Total**: 6,480 words

## Level Mapping

The script automatically maps all formats to numeric levels (1-6):

| Source | Original Label | Numeric Level |
|--------|---------------|---------------|
| GEPT Elementary | 知識 | 1 |
| GEPT Intermediate | 中級 / 中线 | 3 |
| GEPT High-Intermediate | 中高級 / 中高线 | 5 |
| SHERWL | 1-6 | 1-6 |

## Expected Results

After processing all PDFs, you should get:

- **Total words**: ~8,000-10,000 unique words (after deduplication)
- **Level distribution**:
  - Level 1: ~2,000-3,000 words (Elementary + SHERWL Level 1)
  - Level 2: ~1,000 words (SHERWL Level 2)
  - Level 3: ~2,000-3,000 words (Intermediate + SHERWL Level 3)
  - Level 4: ~1,000 words (SHERWL Level 4)
  - Level 5: ~2,000-3,000 words (High-Intermediate + SHERWL Level 5)
  - Level 6: ~1,000 words (SHERWL Level 6)

## Output Files

The script creates three output files:

1. **`data/source/moe_7000.csv`** - CSV format (word, moe_level)
2. **`data/source/moe_7000.json`** - JSON format
3. **`data/source/moe_7000.txt`** - Tab-separated text

## Troubleshooting

### PDF Download Fails

If the download script fails:
1. Try downloading manually from the URLs
2. Check your internet connection
3. Some URLs may require direct browser access

### Extraction Finds Few Words

1. **Check PDF format**: Ensure PDFs are text-based (not scanned images)
2. **Review preview**: The script shows extracted text - verify it looks correct
3. **Try different library**: 
   ```bash
   pip install PyMuPDF  # Alternative to pdfplumber
   ```

### Level Mapping Issues

If levels don't look correct:
1. Check the statistics output - it shows level distribution
2. Review sample words to verify levels make sense
3. The script handles duplicates by keeping the lowest level

### Combining Results

The script automatically:
- Merges words from all PDFs
- Keeps the lowest level if a word appears multiple times
- Deduplicates entries
- Sorts by level and alphabetically

## Next Steps

After extraction:

1. **Verify the data**: Review the CSV file to ensure quality
2. **Check statistics**: Verify level distribution makes sense
3. **Test integration**: The word list should work with your existing codebase
4. **Update scripts**: Other scripts using MOE data will now use real data

## File Structure

```
LexiCraft.xyz/
├── scripts/
│   ├── extract_moe_from_pdf.py      # Main extraction script
│   ├── download_all_moe_pdfs.sh     # Download script
│   └── COMPLETE_MOE_EXTRACTION_GUIDE.md  # This guide
├── downloads/                       # PDF files (created by download script)
│   ├── GEPT_Elementary.pdf
│   ├── GEPT_Intermediate.pdf
│   ├── GEPT_High-Intermediate.pdf
│   └── SHERWL.pdf
└── data/
    └── source/
        ├── moe_7000.csv             # Final output
        ├── moe_7000.json
        └── moe_7000.txt
```

## Additional Resources

- **LTTC GEPT Vocabulary**: https://www.lttc.ntu.edu.tw/en/vocabulary
- **CEEC SHERWL**: https://www.ceec.edu.tw/
- **MOE Website**: https://www.moe.gov.tw/

