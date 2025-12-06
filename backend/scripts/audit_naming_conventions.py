#!/usr/bin/env python3
"""
Naming Convention Audit Script

Scans codebase for old naming conventions and reports what needs to be updated.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Patterns to search for
PATTERNS = {
    "pipeline_phase": [
        r"Phase\s+[0-6]",
        r"Pipeline\s+Phase\s+[0-6]",
        r"phase\s+[0-6]",
    ],
    "enrichment_stage": [
        r"Stage\s+[12]",
        r"stage\s+[12]",
        r"Stage\s+[12]\s+enrichment",
        r"Enrichment\s+Stage",
    ],
    "relationship_phase": [
        r"Relationship\s+Phase\s+[1-5]",
        r"relationship\s+phase\s+[1-5]",
    ],
    "enrichment_generic": [
        r"enrichment",
        r"Enrichment",
        r"ENRICHMENT",
    ],
}

# Files to scan
SCAN_PATTERNS = ["*.md", "*.py"]
SKIP_DIRS = ["venv", "node_modules", "__pycache__", ".git", "migrations"]


def find_files(root_dir="."):
    """Find all files to scan."""
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in filenames:
            if any(filename.endswith(ext.replace("*", "")) for ext in SCAN_PATTERNS):
                filepath = os.path.join(root, filename)
                files.append(filepath)
    
    return files


def scan_file(filepath, patterns):
    """Scan a file for pattern matches."""
    matches = defaultdict(list)
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            
            for pattern_name, pattern_list in patterns.items():
                for pattern in pattern_list:
                    regex = re.compile(pattern, re.IGNORECASE)
                    for line_num, line in enumerate(lines, 1):
                        if regex.search(line):
                            matches[pattern_name].append({
                                'line': line_num,
                                'content': line.strip()[:100],
                                'pattern': pattern
                            })
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return matches


def generate_report():
    """Generate audit report."""
    print("=" * 80)
    print("NAMING CONVENTION AUDIT REPORT")
    print("=" * 80)
    print()
    
    files = find_files()
    print(f"Scanning {len(files)} files...")
    print()
    
    all_matches = defaultdict(lambda: defaultdict(list))
    file_counts = defaultdict(int)
    
    for filepath in files:
        matches = scan_file(filepath, PATTERNS)
        if matches:
            for pattern_type, match_list in matches.items():
                all_matches[pattern_type][filepath] = match_list
                file_counts[pattern_type] += 1
    
    # Report by pattern type
    print("=" * 80)
    print("SUMMARY BY PATTERN TYPE")
    print("=" * 80)
    print()
    
    for pattern_type, files_dict in all_matches.items():
        total_matches = sum(len(matches) for matches in files_dict.values())
        print(f"{pattern_type.upper().replace('_', ' ')}:")
        print(f"  Files affected: {len(files_dict)}")
        print(f"  Total matches: {total_matches}")
        print()
    
    # Detailed report
    print("=" * 80)
    print("DETAILED FINDINGS")
    print("=" * 80)
    print()
    
    for pattern_type, files_dict in sorted(all_matches.items()):
        if not files_dict:
            continue
            
        print(f"\n{pattern_type.upper().replace('_', ' ')}:")
        print("-" * 80)
        
        for filepath, matches in sorted(files_dict.items()):
            print(f"\n  {filepath}:")
            for match in matches[:5]:  # Show first 5 matches per file
                print(f"    Line {match['line']}: {match['content']}")
            if len(matches) > 5:
                print(f"    ... and {len(matches) - 5} more matches")
    
    # Priority files
    print()
    print("=" * 80)
    print("PRIORITY FILES (Most References)")
    print("=" * 80)
    print()
    
    file_totals = defaultdict(int)
    for pattern_type, files_dict in all_matches.items():
        for filepath, matches in files_dict.items():
            file_totals[filepath] += len(matches)
    
    for filepath, count in sorted(file_totals.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {filepath}: {count} matches")
    
    # Recommendations
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("1. Start with files with most matches (Priority 1)")
    print("2. Update core documentation files first")
    print("3. Update code comments/docstrings second")
    print("4. Verify with this script after each batch")
    print()
    print(f"Total files needing updates: {len(file_totals)}")
    print(f"Total matches found: {sum(file_totals.values())}")


if __name__ == "__main__":
    generate_report()


