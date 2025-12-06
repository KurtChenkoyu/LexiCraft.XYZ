"""
Detailed Chinese Translation Analysis
Manual verification of Traditional Chinese usage
"""

from src.database.neo4j_connection import Neo4jConnection

def analyze_chinese_quality(conn):
    print("=" * 60)
    print("CHINESE TRANSLATION QUALITY ANALYSIS")
    print("=" * 60)
    
    with conn.get_session() as session:
        result = session.run("""
            MATCH (s:Sense {enriched: true})
            RETURN s.id, s.definition_zh, s.example_zh, s.definition_en
        """)
        
        for record in result:
            sense_id = record['s.id']
            zh_def = record['s.definition_zh'] or ''
            zh_ex = record['s.example_zh'] or ''
            en_def = record['s.definition_en']
            
            print(f"\nSense: {sense_id}")
            print(f"English: {en_def}")
            print(f"Chinese Def: {zh_def}")
            print(f"Chinese Example: {zh_ex}")
            
            # Key Traditional Chinese characters (that differ from Simplified)
            # Traditional -> Simplified mappings
            trad_only_chars = {
                '銀': '银',  # bank/silver
                '這': '这',  # this
                '張': '张',  # sheet/measure word
                '們': '们',  # plural marker
                '邊': '边',  # side/edge
            }
            
            combined = zh_def + zh_ex
            issues = []
            is_traditional = True
            
            for trad_char, simp_char in trad_only_chars.items():
                if trad_char in combined:
                    print(f"  ✅ Contains Traditional '{trad_char}' (vs Simplified '{simp_char}')")
                if simp_char in combined:
                    issues.append(f"Contains Simplified '{simp_char}' (should be '{trad_char}')")
                    is_traditional = False
            
            # Check for Taiwan-specific naturalness
            # Taiwan uses: 銀行 (not 银行), 這張 (not 这张), 他們 (not 他们)
            taiwan_indicators = ['銀行', '這張', '他們', '河岸邊']
            has_taiwan_usage = any(indicator in combined for indicator in taiwan_indicators)
            
            if is_traditional and has_taiwan_usage:
                print(f"  ✅ Traditional Chinese (繁體) - Taiwan natural")
            elif is_traditional:
                print(f"  ✅ Traditional Chinese (繁體) - May need Taiwan-specific review")
            else:
                print(f"  ❌ Issues found: {', '.join(issues)}")
            
            # Naturalness check
            if '；' in zh_def:  # Traditional semicolon
                print(f"  ✅ Uses Traditional punctuation (；)")
            if '，' in combined:  # Traditional comma
                print(f"  ✅ Uses Traditional punctuation (，)")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            analyze_chinese_quality(conn)
    finally:
        conn.close()

