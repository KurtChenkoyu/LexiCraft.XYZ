#!/usr/bin/env python3
"""
Fetch Taiwan MOE Word List
Downloads the official Taiwan Ministry of Education English vocabulary lists
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError

# Output paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parent.parent / "data" / "source"
OUTPUT_CSV = DATA_DIR / "moe_7000.csv"
OUTPUT_JSON = DATA_DIR / "moe_7000.json"
OUTPUT_TXT = DATA_DIR / "moe_7000.txt"

# Known sources for Taiwan MOE word lists
SOURCES = {
    "sherwl": {
        "name": "Senior High School English Reference Word List (SHERWL)",
        "url": "https://www.ceec.edu.tw/",
        "description": "6,480 words in 6 levels (Level 1-6)"
    },
    "elementary_junior": {
        "name": "Basic English Vocabulary for Elementary and Junior High",
        "url": "https://www.moe.gov.tw/",
        "description": "3,000 words (1,000 essential + 2,000 advanced)"
    },
    "gept": {
        "name": "GEPT Word Lists (LTTC)",
        "url": "https://www.lttc.ntu.edu.tw/en/vocabulary",
        "description": "Elementary, Intermediate, High-Intermediate levels"
    }
}


def normalize_word(word: str) -> Optional[str]:
    """Normalize word to lowercase and remove extra whitespace"""
    if not word:
        return None
    word = word.strip().lower()
    # Remove non-alphabetic characters except hyphens and apostrophes
    word = re.sub(r'[^a-z\-\']', '', word)
    return word if word else None


def fetch_from_github() -> Optional[Dict[str, int]]:
    """Try to fetch Taiwan MOE word list from GitHub repositories"""
    print("Searching GitHub for Taiwan MOE word lists...")
    
    # Common GitHub repositories that might have this data
    github_repos = [
        "https://raw.githubusercontent.com/",
        # Add known repos if found
    ]
    
    # Try common patterns
    potential_urls = [
        # Add specific URLs if known
    ]
    
    for url in potential_urls:
        try:
            with urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
                print(f"Found data at: {url}")
                # Parse the data based on format
                return parse_word_list(content)
        except (URLError, Exception) as e:
            continue
    
    return None


def parse_word_list(content: str, format_type: str = "auto") -> Dict[str, int]:
    """Parse word list from various formats"""
    words = {}
    
    if format_type == "auto":
        # Try to detect format
        if content.strip().startswith("{"):
            format_type = "json"
        elif "," in content.split("\n")[0]:
            format_type = "csv"
        else:
            format_type = "txt"
    
    if format_type == "csv":
        reader = csv.DictReader(content.splitlines())
        for row in reader:
            word = normalize_word(row.get("word", ""))
            level = row.get("level", row.get("moe_level", ""))
            if word and level:
                try:
                    words[word] = int(level)
                except ValueError:
                    pass
    elif format_type == "json":
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                word = normalize_word(item.get("word", ""))
                level = item.get("level", item.get("moe_level", ""))
                if word and level:
                    try:
                        words[word] = int(level)
                    except ValueError:
                        pass
        elif isinstance(data, dict):
            for word, level in data.items():
                word = normalize_word(word)
                if word and level:
                    try:
                        words[word] = int(level) if isinstance(level, (int, str)) else 0
                    except ValueError:
                        pass
    else:  # txt format
        for line_num, line in enumerate(content.splitlines(), 1):
            parts = line.strip().split()
            if parts:
                word = normalize_word(parts[0])
                level = 1
                if len(parts) > 1:
                    try:
                        level = int(parts[1])
                    except ValueError:
                        level = 1
                if word:
                    words[word] = level
    
    return words


def create_combined_moe_list() -> Dict[str, int]:
    """
    Create a comprehensive MOE word list by combining known sources.
    This is a fallback if we can't fetch from official sources.
    """
    print("Creating combined MOE word list from known curriculum sources...")
    
    # This would ideally fetch from:
    # 1. SHERWL (6,480 words, levels 1-6)
    # 2. Elementary/Junior High list (3,000 words)
    # 3. GEPT lists
    
    # For now, we'll create a structure that can be populated
    # The actual word list would need to be obtained from:
    # - Official MOE website
    # - CEEC website (for SHERWL)
    # - LTTC website (for GEPT)
    # - Or manually compiled from official documents
    
    words = {}
    
    print("⚠️  Note: This script needs the actual word list data.")
    print("   Please provide one of the following:")
    print("   1. A CSV/JSON/TXT file with the MOE word list")
    print("   2. A URL to download the word list from")
    print("   3. Manual compilation from official MOE sources")
    
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


def load_from_file(file_path: Path) -> Optional[Dict[str, int]]:
    """Load word list from a local file"""
    if not file_path.exists():
        return None
    
    print(f"Loading word list from: {file_path}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Detect format
    if file_path.suffix == '.json':
        return parse_word_list(content, "json")
    elif file_path.suffix == '.csv':
        return parse_word_list(content, "csv")
    else:
        return parse_word_list(content, "txt")


def main():
    """Main execution"""
    print("=" * 60)
    print("Taiwan MOE Word List Fetcher")
    print("=" * 60)
    
    words = None
    
    # Try to load from existing file first
    if OUTPUT_CSV.exists():
        print(f"\nFound existing file: {OUTPUT_CSV}")
        response = input("Do you want to replace it? (y/n): ").strip().lower()
        if response != 'y':
            print("Keeping existing file.")
            return
    
    # Try to fetch from GitHub
    words = fetch_from_github()
    
    # If not found, try to create combined list
    if not words:
        words = create_combined_moe_list()
    
    # If we have words, save them
    if words:
        save_word_list(words, OUTPUT_CSV, OUTPUT_JSON, OUTPUT_TXT)
        
        # Print statistics
        level_counts = {}
        for word, level in words.items():
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"\n📊 Statistics:")
        print(f"   Total words: {len(words)}")
        print(f"   Level distribution:")
        for level in sorted(level_counts.keys()):
            print(f"      Level {level}: {level_counts[level]} words")
    else:
        print("\n❌ No word list data found.")
        print("\nTo get the real Taiwan MOE word list:")
        print("1. Visit https://www.ceec.edu.tw/ for SHERWL (6,480 words)")
        print("2. Visit https://www.lttc.ntu.edu.tw/en/vocabulary for GEPT lists")
        print("3. Check official MOE website for elementary/junior high lists")
        print("4. Or provide a CSV/JSON/TXT file with the word list")
        print("\nYou can also manually download the official lists and save them as:")
        print(f"   {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

