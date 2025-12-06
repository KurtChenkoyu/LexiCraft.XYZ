# Extract Taiwan MOE Word List from PDF Files

This guide shows you how to extract word lists from PDF files containing Taiwan MOE vocabulary.

## Quick Start

### 1. Install Required Libraries

```bash
# Install pdfplumber (recommended - best for tables)
pip install pdfplumber

# Or install PyMuPDF (alternative - faster)
pip install PyMuPDF

# Or install PyPDF2 (basic option)
pip install PyPDF2
```

Or install all at once:
```bash
pip install -r scripts/requirements_pdf.txt
```

### 2. Run the Extraction Script

```bash
python3 scripts/extract_moe_from_pdf.py path/to/your/pdf/file.pdf
```

For multiple PDF files:
```bash
python3 scripts/extract_moe_from_pdf.py file1.pdf file2.pdf file3.pdf
```

### 3. Output

The script will create:
- `data/source/moe_7000.csv` - CSV format (word, moe_level)
- `data/source/moe_7000.json` - JSON format
- `data/source/moe_7000.txt` - Tab-separated text

## Supported PDF Formats

The script can handle various PDF formats:

1. **Table Format** - Words and levels in columns
   ```
   Word        Level
   apple       1
   book        1
   difficult   3
   ```

2. **List Format** - Words with levels inline
   ```
   apple 1
   book 1
   difficult 3
   ```

3. **Mixed Format** - Combination of tables and lists

## How It Works

1. **Text Extraction**: Extracts all text from the PDF using available libraries
2. **Pattern Matching**: Identifies words and their associated levels using regex patterns
3. **Normalization**: Converts words to lowercase and cleans them
4. **Deduplication**: If a word appears multiple times, keeps the lowest level
5. **Export**: Saves in multiple formats for use in the codebase

## Troubleshooting

### No words extracted

If the script extracts text but finds no words:

1. **Check the PDF format**: Some PDFs are scanned images (not text-based)
   - Solution: Use OCR software first, or try a different PDF source

2. **Check the text preview**: The script shows a preview of extracted text
   - Look for patterns like "word level" or "word, level"
   - The script may need adjustment for your specific PDF format

3. **Manual adjustment**: If the PDF has a unique format, you may need to:
   - Adjust the regex patterns in `parse_word_list_from_text()`
   - Or extract text manually and use the text processing script

### Installation errors

If you get import errors:

```bash
# Try installing with pip3 instead of pip
pip3 install pdfplumber

# Or install in a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pdfplumber
```

### PDF is scanned/image-based

If the PDF contains images instead of text:

1. Use OCR software (like Tesseract) to convert images to text first
2. Or find a text-based version of the PDF
3. Or manually type the word list into a CSV file

## Example Output

After running the script, you'll see:

```
============================================================
Extracting Taiwan MOE Word List from PDF
============================================================

Extracting text from: sherwl.pdf
  Using pdfplumber...

Extracted 125000 characters of text
Preview (first 500 chars):
...

Attempting to parse as table format...
  Found 3240 words from table format
Attempting to parse as general text...
  Found 6480 words from text format

✅ Total unique words extracted: 6480

✅ Saved 6480 words to:
   - data/source/moe_7000.csv
   - data/source/moe_7000.json
   - data/source/moe_7000.txt

📊 Statistics:
   Total words: 6480
   Level distribution:
      Level 1: 1080 words
      Level 2: 1080 words
      Level 3: 1080 words
      Level 4: 1080 words
      Level 5: 1080 words
      Level 6: 1080 words
```

## Next Steps

After extracting the word list:

1. **Verify the data**: Check that words and levels look correct
2. **Review statistics**: Ensure level distribution makes sense
3. **Test integration**: The word list should work with your existing codebase
4. **Update scripts**: Other scripts that use the MOE word list will now use real data

## Tips

- **Multiple PDFs**: If you have separate PDFs for different levels, process them all at once
- **Quality check**: Review the extracted words to ensure accuracy
- **Backup**: Keep the original PDFs as backup
- **Format**: The script handles various formats, but some PDFs may need manual adjustment

## Alternative: Manual Entry

If PDF extraction doesn't work well, you can:

1. Copy text from the PDF manually
2. Paste into a text file
3. Use the text processing script: `scripts/fetch_taiwan_moe_wordlist.py`

