# Extract GEPT Word Lists from PDF

This guide shows you how to extract word lists from the GEPT (General English Proficiency Test) PDF files from LTTC.

## GEPT PDF Sources

- **High-Intermediate**: https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf
- **Intermediate**: Check https://www.lttc.ntu.edu.tw/en/vocabulary for other levels
- **Elementary**: Check https://www.lttc.ntu.edu.tw/en/vocabulary for other levels

## Quick Start

### Step 1: Download the PDF

You can download the PDF directly:
```bash
# Download High-Intermediate word list
curl -o GEPT_High-Intermediate.pdf https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf
```

Or download it manually from: https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf

### Step 2: Install PDF Library

```bash
pip install pdfplumber
```

### Step 3: Extract the Word List

```bash
python3 scripts/extract_moe_from_pdf.py GEPT_High-Intermediate.pdf
```

If you have multiple GEPT PDFs (Elementary, Intermediate, High-Intermediate):
```bash
python3 scripts/extract_moe_from_pdf.py GEPT_Elementary.pdf GEPT_Intermediate.pdf GEPT_High-Intermediate.pdf
```

## GEPT Level Mapping

The script automatically converts GEPT Chinese level labels to numeric levels:

| Chinese Label | English | Numeric Level |
|--------------|---------|--------------|
| 纵线 / 幼级 | Elementary | 1 |
| 結構 | Structural | 1 |
| 中线 / 中級 | Intermediate | 3 |
| 中高线 / 中高級 | High-Intermediate | 5 |

## PDF Format

The GEPT PDFs contain tables with these columns:
- **字集** (Word) - The English word
- **词源** (Part of Speech) - noun, verb, adj., etc.
- **中文** (Chinese Translation)
- **注释** (Notes)
- **统数** (Level) - Chinese level label
- **甲卅字集** (Additional classification)

The script automatically:
1. Extracts text from the PDF
2. Identifies the table structure
3. Extracts words from the "字集" column
4. Converts level labels from "统数" column to numeric levels
5. Saves to `data/source/moe_7000.csv`

## Expected Output

After running the script, you should see:

```
============================================================
Extracting Taiwan MOE Word List from PDF
============================================================

Extracting text from: GEPT_High-Intermediate.pdf
  Using pdfplumber...

Extracted 370205 characters of text
Preview (first 500 chars):
...

Attempting to parse as table format...
  Found 2000+ words from table format
Attempting to parse as general text...
  Found 2000+ words from text format

✅ Total unique words extracted: 2000+

✅ Saved 2000+ words to:
   - data/source/moe_7000.csv
   - data/source/moe_7000.json
   - data/source/moe_7000.txt

📊 Statistics:
   Total words: 2000+
   Level distribution:
      Level 1: XXX words (Elementary)
      Level 3: XXX words (Intermediate)
      Level 5: XXX words (High-Intermediate)
```

## Combining Multiple GEPT Levels

If you download all three GEPT levels, process them together:

```bash
python3 scripts/extract_moe_from_pdf.py \
  GEPT_Elementary.pdf \
  GEPT_Intermediate.pdf \
  GEPT_High-Intermediate.pdf
```

The script will:
- Extract words from all PDFs
- Merge them together
- Keep the lowest level if a word appears in multiple levels
- Save the combined list

## Verification

After extraction, check the CSV file:

```bash
head -20 data/source/moe_7000.csv
```

You should see:
```csv
word,moe_level
abandon,5
abbey,5
abbreviate,5
...
```

## Notes

- The GEPT High-Intermediate list contains approximately 2,000+ words
- Words are categorized by difficulty level
- Some words may appear in multiple entries (different parts of speech)
- The script handles duplicates by keeping the lowest level

## Troubleshooting

### If extraction finds fewer words than expected:

1. **Check the PDF format**: The script works best with text-based PDFs (not scanned images)
2. **Review the preview**: The script shows a preview of extracted text - check if it looks correct
3. **Try a different PDF library**: If pdfplumber doesn't work well, try PyMuPDF:
   ```bash
   pip install PyMuPDF
   ```

### If levels are incorrect:

The script maps GEPT levels to numeric levels. If you need different mappings, edit the `parse_gept_level()` function in the script.

## Next Steps

After extracting the GEPT word list:

1. **Verify the data**: Check that words and levels look correct
2. **Combine with other sources**: You can combine GEPT with SHERWL or other MOE lists
3. **Use in your codebase**: The CSV file is ready to use with your existing scripts

## Additional Resources

- **LTTC GEPT Vocabulary**: https://www.lttc.ntu.edu.tw/en/vocabulary
- **GEPT High-Intermediate PDF**: https://www.lttc.ntu.edu.tw/resources/GEPT/GEPT_High-Intermediate.pdf

