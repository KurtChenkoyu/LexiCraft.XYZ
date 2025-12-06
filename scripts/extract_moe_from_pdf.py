#!/usr/bin/env python3
"""
Extract Taiwan MOE Word List from PDF files
Handles various PDF formats and extracts word lists with levels
"""

import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Output paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parent.parent / "data" / "source"
OUTPUT_CSV = DATA_DIR / "moe_7000.csv"
OUTPUT_JSON = DATA_DIR / "moe_7000.json"
OUTPUT_TXT = DATA_DIR / "moe_7000.txt"


def normalize_word(word: str) -> Optional[str]:
    """Normalize word to lowercase and clean"""
    if not word:
        return None
    word = word.strip().lower()
    # Remove non-alphabetic characters except hyphens and apostrophes
    word = re.sub(r'[^a-z\-\']', '', word)
    return word if word and len(word) > 1 else None


def extract_text_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber (best for tables)"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_pypdf2(pdf_path: Path) -> str:
    """Extract text using PyPDF2"""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


def extract_text_pymupdf(pdf_path: Path) -> str:
    """Extract text using PyMuPDF (fitz)"""
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using available library"""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    print(f"Extracting text from: {pdf_path.name}")
    
    # Try pdfplumber first (best for structured data)
    if HAS_PDFPLUMBER:
        try:
            print("  Using pdfplumber...")
            return extract_text_pdfplumber(pdf_path)
        except Exception as e:
            print(f"  pdfplumber failed: {e}")
    
    # Try PyMuPDF
    if HAS_PYMUPDF:
        try:
            print("  Using PyMuPDF...")
            return extract_text_pymupdf(pdf_path)
        except Exception as e:
            print(f"  PyMuPDF failed: {e}")
    
    # Try PyPDF2
    if HAS_PYPDF2:
        try:
            print("  Using PyPDF2...")
            return extract_text_pypdf2(pdf_path)
        except Exception as e:
            print(f"  PyPDF2 failed: {e}")
    
    raise ImportError(
        "No PDF library available. Install one of:\n"
        "  pip install pdfplumber  # Recommended\n"
        "  pip install PyMuPDF\n"
        "  pip install PyPDF2"
    )


def parse_word_list_from_text(text: str, pdf_type: str = "auto") -> Dict[str, int]:
    """
    Parse word list from extracted PDF text.
    Handles various formats:
    - "word level" (e.g., "apple 1")
    - "word, level" (e.g., "apple, 1")
    - "level word" (e.g., "1 apple")
    - Table format with columns
    - GEPT format with Chinese level labels
    """
    words = {}
    lines = text.split('\n')
    
    # Patterns to match words with levels
    patterns = [
        # Pattern 1: "word level" or "word, level"
        re.compile(r'^([a-z\-\']+)[\s,]+(\d+)$', re.IGNORECASE),
        # Pattern 2: "level word"
        re.compile(r'^(\d+)[\s,]+([a-z\-\']+)$', re.IGNORECASE),
        # Pattern 3: "word\tlevel" (tab-separated)
        re.compile(r'^([a-z\-\']+)\t+(\d+)$', re.IGNORECASE),
        # Pattern 4: Word followed by number in same line
        re.compile(r'([a-z\-\']+)[\s,]+(\d+)', re.IGNORECASE),
        # Pattern 5: Word followed by Chinese level label
        re.compile(r'([a-z\-\']+)[\s,]+(纵线|幼级|結構|中线|中級|中高线|中高級|知識|扫描)', re.IGNORECASE),
    ]
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Try each pattern
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                groups = match.groups()
                
                # Determine which group is word and which is level
                word = None
                level = None
                
                for group in groups:
                    if group.isdigit():
                        level = int(group)
                    elif re.match(r'^[a-z\-\']+$', group, re.IGNORECASE):
                        word = normalize_word(group)
                    else:
                        # Might be Chinese level label
                        parsed_level = parse_gept_level(group, pdf_type)
                        if parsed_level:
                            level = parsed_level
                
                # For Elementary PDFs, if no level found, default to 1
                if word and not level and pdf_type == "elementary":
                    level = 1
                
                if word and level and 1 <= level <= 6:
                    # Keep the lowest level if word appears multiple times
                    if word not in words or words[word] > level:
                        words[word] = level
                    break
    
    return words


def parse_gept_level(level_str: str, pdf_type: str = "auto") -> Optional[int]:
    """Convert GEPT Chinese level labels to numeric levels"""
    if not level_str:
        return None
    
    level_str = level_str.strip()
    
    # GEPT level mappings (based on the PDF structure)
    # Elementary: "初級" = Level 1
    # Intermediate: "中級" = Level 3
    # High-Intermediate: "中高級" = Level 5
    # SHERWL: Numeric levels 1-6
    
    # General GEPT level mappings
    level_mapping = {
        '初級': 1,  # Elementary
        '纵线': 1,
        '幼级': 1,
        '結構': 1,
        '知識': 1,  # Elementary (alternative)
        '中线': 3,
        '中級': 3,  # Intermediate
        '中高线': 5,
        '中高級': 5,  # High-Intermediate
        '扫描': 1,  # Sometimes appears in Elementary PDFs
    }
    
    # Check exact matches first
    if level_str in level_mapping:
        return level_mapping[level_str]
    
    # Check if it contains any of the keywords
    for keyword, level in level_mapping.items():
        if keyword in level_str:
            return level
    
    # Check for numeric levels (L1, L2, etc. or just numbers)
    match = re.search(r'L?(\d)', level_str, re.IGNORECASE)
    if match:
        level_num = int(match.group(1))
        if 1 <= level_num <= 6:
            return level_num
    
    # SHERWL format: might have level numbers directly
    if level_str.isdigit():
        level_num = int(level_str)
        if 1 <= level_num <= 6:
            return level_num
    
    return None


def parse_table_format(text: str, pdf_type: str = "auto") -> Dict[str, int]:
    """Parse if the PDF contains table data"""
    words = {}
    
    # Look for table-like structures
    # Common patterns:
    # - Columns separated by spaces/tabs
    # - Headers like "Word", "Level", "字彙", "等級", "字集"
    
    lines = text.split('\n')
    header_found = False
    word_col = None
    level_col = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for header row
        # GEPT Elementary: 字彙, 同類, 中文, 同類, 規劃, 學術字彙
        # GEPT Intermediate/High-Intermediate: 字集, 词源, 中文, 注释, 统数, 甲卅字集
        # SHERWL: Various formats
        if not header_found:
            header_lower = line.lower()
            # Check for GEPT headers or English headers
            if any(keyword in header_lower for keyword in ['word', '字彙', 'vocabulary', '字集', 'level', '等級', '统数', '規劃', '同類']):
                # Try to identify column positions
                # GEPT format uses | separators or multiple spaces
                parts = re.split(r'\s*\|\s*|\s{2,}|\t', line)
                parts = [p.strip() for p in parts if p.strip()]
                
                for i, part in enumerate(parts):
                    part_lower = part.lower().strip()
                    if any(keyword in part_lower for keyword in ['word', '字彙', 'vocabulary', '字集']):
                        word_col = i
                    elif any(keyword in part_lower for keyword in ['level', '等級', '统数', '規劃']):
                        level_col = i
                
                header_found = True
                continue
        
        # Parse data rows
        if header_found:
            # For GEPT PDFs, format is: word pos chinese notes level [academic]
            # Columns are separated by single spaces
            # Example: "a art. 一(個) 後接母音開頭之字時為 an 初級"
            # Example: "ability noun 能力、才能 初級"
            
            # Split by spaces, but be careful with Chinese text which may contain spaces
            # Strategy: word is first token, level is usually last or second-to-last token
            parts = line.split()
            
            if len(parts) >= 2:
                word = None
                level = None
                
                # First token should be the word
                if len(parts) > 0:
                    first_part = parts[0].strip()
                    normalized = normalize_word(first_part)
                    if normalized and len(normalized) >= 1 and re.match(r'^[a-z\-\']+$', normalized):
                        word = normalized
                
                # Level is usually in the last 2 tokens (last token or second-to-last)
                # Check last token first
                if len(parts) >= 1:
                    last_part = parts[-1].strip()
                    parsed_level = parse_gept_level(last_part, pdf_type)
                    if parsed_level:
                        level = parsed_level
                
                # If not found, check second-to-last token
                if not level and len(parts) >= 2:
                    second_last = parts[-2].strip()
                    parsed_level = parse_gept_level(second_last, pdf_type)
                    if parsed_level:
                        level = parsed_level
                
                # Also check all tokens for level indicators (in case format varies)
                if not level:
                    for part in parts:
                        part = part.strip()
                        parsed_level = parse_gept_level(part, pdf_type)
                        if parsed_level:
                            level = parsed_level
                            break
                
                # For Elementary PDFs, if no level found, default to 1
                if word and not level and pdf_type == "elementary":
                    level = 1
                
                if word and level:
                    if word not in words or words[word] > level:
                        words[word] = level
    
    return words


def detect_pdf_type(text: str, filename: str) -> str:
    """Detect the type of PDF based on content and filename"""
    filename_lower = filename.lower()
    text_lower = text.lower()
    
    # Check filename first
    if "elementary" in filename_lower or "初級" in filename_lower:
        return "elementary"
    elif "intermediate" in filename_lower or "中級" in filename_lower:
        return "intermediate"
    elif "high-intermediate" in filename_lower or "中高級" in filename_lower:
        return "high-intermediate"
    elif "sherwl" in filename_lower or "參考詞彙" in filename_lower or "高中英文" in filename_lower:
        return "sherwl"
    
    # Check content
    if "知識" in text and "字彙" in text:
        return "elementary"
    elif "中高級" in text or "中高线" in text:
        return "high-intermediate"
    elif "中級" in text or "中线" in text:
        return "intermediate"
    elif "參考詞彙" in text or "高中英文" in text:
        return "sherwl"
    
    return "auto"


def extract_words_from_pdf(pdf_path: Path) -> Dict[str, int]:
    """Main function to extract words from PDF"""
    print(f"\n{'='*60}")
    print(f"Extracting Taiwan MOE Word List from PDF")
    print(f"File: {pdf_path.name}")
    print(f"{'='*60}\n")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    
    # Detect PDF type
    pdf_type = detect_pdf_type(text, pdf_path.name)
    print(f"Detected PDF type: {pdf_type}")
    
    print(f"\nExtracted {len(text)} characters of text")
    print(f"Preview (first 500 chars):\n{text[:500]}...\n")
    
    # Try table format first (more structured)
    print("Attempting to parse as table format...")
    words_table = parse_table_format(text, pdf_type)
    print(f"  Found {len(words_table)} words from table format")
    
    # Try general text parsing
    print("Attempting to parse as general text...")
    words_text = parse_word_list_from_text(text, pdf_type)
    print(f"  Found {len(words_text)} words from text format")
    
    # Combine results (prefer table format, but merge both)
    words = words_table.copy()
    for word, level in words_text.items():
        if word not in words or words[word] > level:
            words[word] = level
    
    print(f"\n✅ Total unique words extracted: {len(words)}")
    
    return words


def save_word_list(words: Dict[str, int], output_csv: Path, output_json: Path, output_txt: Path):
    """Save word list to multiple formats"""
    # Ensure output directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by level, then alphabetically
    sorted_words = sorted(words.items(), key=lambda x: (x[1], x[0]))
    
    # Save as CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'moe_level'])
        for word, level in sorted_words:
            writer.writerow([word, level])
    
    # Save as JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    
    # Save as TXT (one word per line)
    with open(output_txt, 'w', encoding='utf-8') as f:
        for word, level in sorted_words:
            f.write(f"{word}\t{level}\n")
    
    print(f"\n✅ Saved {len(words)} words to:")
    print(f"   - {output_csv}")
    print(f"   - {output_json}")
    print(f"   - {output_txt}")


def main():
    """Main execution"""
    
    if len(sys.argv) < 2:
        print("Usage: python extract_moe_from_pdf.py <pdf_file_path>")
        print("\nExample:")
        print("  python extract_moe_from_pdf.py ~/Downloads/sherwl.pdf")
        print("\nYou can also specify multiple PDF files:")
        print("  python extract_moe_from_pdf.py file1.pdf file2.pdf")
        sys.exit(1)
    
    all_words = {}
    
    for pdf_path_str in sys.argv[1:]:
        pdf_path = Path(pdf_path_str)
        
        if not pdf_path.exists():
            print(f"❌ Error: File not found: {pdf_path}")
            continue
        
        try:
            words = extract_words_from_pdf(pdf_path)
            
            # Merge with existing words (keep lowest level)
            for word, level in words.items():
                if word not in all_words or all_words[word] > level:
                    all_words[word] = level
            
        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if all_words:
        save_word_list(all_words, OUTPUT_CSV, OUTPUT_JSON, OUTPUT_TXT)
        
        # Print statistics
        level_counts = {}
        for word, level in all_words.items():
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"\n📊 Statistics:")
        print(f"   Total words: {len(all_words)}")
        print(f"   Level distribution:")
        for level in sorted(level_counts.keys()):
            print(f"      Level {level}: {level_counts[level]} words")
        
        # Show sample words
        print(f"\n📝 Sample words (first 20):")
        sorted_words = sorted(all_words.items(), key=lambda x: (x[1], x[0]))
        for word, level in sorted_words[:20]:
            print(f"   {word:20s} (Level {level})")
    else:
        print("\n❌ No words extracted from PDF files.")


if __name__ == "__main__":
    main()

