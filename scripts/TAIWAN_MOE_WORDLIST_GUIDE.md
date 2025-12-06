# Taiwan MOE Word List - How to Get the Real Data

This guide explains how to obtain the official Taiwan Ministry of Education (MOE) English vocabulary word lists.

## Official Sources

### 1. SHERWL (Senior High School English Reference Word List)
- **Source**: College Entrance Examination Center (CEEC)
- **Words**: 6,480 words
- **Levels**: 6 levels (1,080 words per level)
- **Website**: https://www.ceec.edu.tw/
- **Description**: Official word list for college entrance examinations
- **Format**: Usually available as PDF or Excel files

### 2. Elementary/Junior High School Word List
- **Source**: Taiwan Ministry of Education
- **Words**: 3,000 words
  - 1,000 essential words (for Basic Competency Test)
  - 2,000 advanced words
- **Website**: https://www.moe.gov.tw/
- **Description**: Basic English vocabulary for elementary and junior high students
- **Published**: 2003

### 3. GEPT Word Lists
- **Source**: Language Training and Testing Center (LTTC)
- **Website**: https://www.lttc.ntu.edu.tw/en/vocabulary
- **Levels**: 
  - Elementary
  - Intermediate
  - High-Intermediate
- **Description**: Word lists aligned with General English Proficiency Test
- **Features**: Includes Chinese definitions and pronunciation guides

## How to Obtain the Data

### Option 1: Download from Official Websites

1. **SHERWL (Recommended for comprehensive list)**:
   - Visit https://www.ceec.edu.tw/
   - Look for "高中英文參考字彙表" or "Senior High School English Reference Word List"
   - Download the Excel or PDF file
   - Convert to CSV format if needed

2. **Elementary/Junior High List**:
   - Visit https://www.moe.gov.tw/
   - Search for "國民中小學英語基本字彙" or "Basic English Vocabulary"
   - Download the official document

3. **GEPT Lists**:
   - Visit https://www.lttc.ntu.edu.tw/en/vocabulary
   - Download word lists for each level
   - Combine into a single list if needed

### Option 2: Use the Processing Script

Once you have the word list data (in CSV, JSON, or TXT format), use the processing script:

```bash
python3 scripts/fetch_taiwan_moe_wordlist.py
```

Or if you have a file to process:

```python
from scripts.fetch_taiwan_moe_wordlist import load_from_file, save_word_list
from pathlib import Path

# Load your word list file
words = load_from_file(Path("path/to/your/wordlist.csv"))

# Save in the required format
output_csv = Path("data/source/moe_7000.csv")
output_json = Path("data/source/moe_7000.json")
output_txt = Path("data/source/moe_7000.txt")

save_word_list(words, output_csv, output_json, output_txt)
```

### Option 3: Manual Compilation

If you have access to the official documents:

1. Extract words and their levels from the official PDF/Excel files
2. Create a CSV file with columns: `word,moe_level`
3. Save it as `data/source/moe_7000.csv`

**CSV Format:**
```csv
word,moe_level
the,1
be,1
to,1
of,1
and,1
...
```

## Expected File Format

The script expects a file with the following format:

**CSV Format (Preferred):**
```csv
word,moe_level
apple,1
book,1
cat,1
difficult,3
...
```

**JSON Format:**
```json
{
  "apple": 1,
  "book": 1,
  "cat": 1,
  "difficult": 3
}
```

**TXT Format:**
```
apple 1
book 1
cat 1
difficult 3
```

## MOE Level System

The Taiwan MOE uses a 6-level system:
- **Level 1**: Most basic/elementary words
- **Level 2**: Basic words
- **Level 3**: Intermediate words
- **Level 4**: Upper-intermediate words
- **Level 5**: Advanced words
- **Level 6**: Most advanced words

## Combining Multiple Sources

If you have multiple word lists (e.g., SHERWL + Elementary list), you can combine them:

1. Load each list separately
2. Merge them, keeping the lowest level for each word (most basic level)
3. Save the combined list

## Verification

After obtaining the word list, verify:
- Total word count matches expected (~7,000 for combined lists)
- All words are in lowercase
- Levels are between 1-6
- No duplicate words (or duplicates handled correctly)

## Current Status

The current `data/source/moe_7000.csv` file contains placeholder data and needs to be replaced with the real Taiwan MOE word list.

## Next Steps

1. Download the official word list from one of the sources above
2. Convert it to CSV format if needed
3. Run the processing script to format it correctly
4. Verify the data matches the expected format
5. Update the codebase to use the real word list

## Additional Resources

- **CEEC Website**: https://www.ceec.edu.tw/
- **MOE Website**: https://www.moe.gov.tw/
- **LTTC Website**: https://www.lttc.ntu.edu.tw/
- **GEPT Vocabulary**: https://www.lttc.ntu.edu.tw/en/vocabulary

