"""
Adversary Builder: The "Hunter" Logic (V7.1)

Builds CONFUSED_WITH relationships for trap generation in LexiSurvey.

The Hunter Algorithm:
- Filter A (Morphology): Levenshtein Distance <= 2
- Filter B (Phonetic): Sound-alike detection (optional)
- Filter C (Semantic): Existing RELATED_TO edges flagged as semantic traps

Goal: Find "Trap Candidates" for high-frequency words (Rank 1-4000).
"""

import Levenshtein
from typing import List, Dict, Tuple, Optional
from src.database.neo4j_connection import Neo4jConnection

# Optional: Phonetic matching (requires Fuzzy library)
try:
    from fuzzy import soundex, metaphone
    PHONETIC_AVAILABLE = True
except ImportError:
    PHONETIC_AVAILABLE = False
    print("⚠️  Fuzzy library not available. Phonetic matching disabled.")


class AdversaryBuilder:
    """
    The "Hunter" - Finds trap candidates using multiple filters.
    """
    
    def __init__(self, conn: Neo4jConnection, max_rank: int = 4000):
        """
        Initialize the Adversary Builder.
        
        Args:
            conn: Neo4j connection
            max_rank: Maximum frequency rank to process (default: 4000)
        """
        self.conn = conn
        self.max_rank = max_rank
        self.stats = {
            "morphology": 0,
            "phonetic": 0,
            "semantic": 0,
            "total": 0
        }
    
    def run(self, dry_run: bool = False):
        """
        Execute the Hunter algorithm to build CONFUSED_WITH relationships.
        
        Args:
            dry_run: If True, only report what would be created (no writes)
        """
        print(f"🔍 Starting Adversary Builder (Hunter Logic V7.1)...")
        print(f"   Target: Words with frequency_rank <= {self.max_rank}")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}\n")
        
        with self.conn.get_session() as session:
            # 1. Fetch high-frequency words
            words = self._fetch_high_frequency_words(session)
            print(f"📊 Found {len(words)} high-frequency words to process\n")
            
            # 2. Process each word through Hunter filters
            for i, word in enumerate(words, 1):
                if i % 100 == 0:
                    print(f"   Progress: {i}/{len(words)} words processed...")
                
                self._hunt_traps(session, word, dry_run)
            
            # 3. Report results
            self._print_summary(dry_run)
    
    def _fetch_high_frequency_words(self, session) -> List[str]:
        """
        Fetch all words with frequency_rank <= max_rank.
        
        Returns:
            List of word names
        """
        result = session.run("""
            MATCH (w:Word)
            WHERE w.frequency_rank <= $max_rank
            RETURN w.name as word
            ORDER BY w.frequency_rank ASC
        """, max_rank=self.max_rank)
        
        return [record["word"] for record in result]
    
    def _hunt_traps(self, session, source_word: str, dry_run: bool):
        """
        Apply all Hunter filters to find trap candidates for a word.
        
        Args:
            session: Neo4j session
            source_word: Source word to find traps for
            dry_run: If True, don't create relationships
        """
        # Filter A: Morphology (Levenshtein Distance)
        morphology_traps = self._filter_morphology(session, source_word)
        
        # Filter B: Phonetic (Sound-alikes)
        phonetic_traps = self._filter_phonetic(session, source_word) if PHONETIC_AVAILABLE else []
        
        # Filter C: Semantic (Existing RELATED_TO)
        semantic_traps = self._filter_semantic(session, source_word)
        
        # Combine and deduplicate
        all_traps = self._combine_traps(morphology_traps, phonetic_traps, semantic_traps)
        
        # Create relationships
        for trap_word, reason, distance in all_traps:
            if not dry_run:
                self._create_confused_with_relationship(session, source_word, trap_word, reason, distance)
            else:
                print(f"   [DRY RUN] Would create: {source_word} -[:CONFUSED_WITH {{reason: '{reason}', distance: {distance}}}]-> {trap_word}")
    
    def _filter_morphology(self, session, source_word: str) -> List[Tuple[str, str, int]]:
        """
        Filter A: Find words with Levenshtein Distance <= 2.
        
        Examples: adapt/adopt, affect/effect, desert/dessert
        
        Returns:
            List of (trap_word, reason, distance) tuples
        """
        traps = []
        
        # Fetch all words in similar rank range (±500) for efficiency
        result = session.run("""
            MATCH (source:Word {name: $source})
            MATCH (target:Word)
            WHERE target.frequency_rank <= $max_rank
              AND target.name <> $source
              AND abs(target.frequency_rank - source.frequency_rank) <= 500
            RETURN target.name as word
        """, source=source_word, max_rank=self.max_rank)
        
        candidates = [record["word"] for record in result]
        
        for candidate in candidates:
            distance = Levenshtein.distance(source_word.lower(), candidate.lower())
            
            if distance <= 2 and distance > 0:  # Distance > 0 excludes identical words
                traps.append((candidate, "Look-alike", distance))
                self.stats["morphology"] += 1
        
        return traps
    
    def _filter_phonetic(self, session, source_word: str) -> List[Tuple[str, str, int]]:
        """
        Filter B: Find sound-alike words using Metaphone.
        
        Returns:
            List of (trap_word, reason, distance) tuples
        """
        if not PHONETIC_AVAILABLE:
            return []
        
        traps = []
        source_meta = metaphone(source_word.lower())
        
        # Fetch candidate words
        result = session.run("""
            MATCH (source:Word {name: $source})
            MATCH (target:Word)
            WHERE target.frequency_rank <= $max_rank
              AND target.name <> $source
              AND abs(target.frequency_rank - source.frequency_rank) <= 500
            RETURN target.name as word
        """, source=source_word, max_rank=self.max_rank)
        
        candidates = [record["word"] for record in result]
        
        for candidate in candidates:
            candidate_meta = metaphone(candidate.lower())
            
            # Check if metaphone codes match
            if source_meta and candidate_meta and source_meta == candidate_meta:
                # Calculate Levenshtein distance for the distance property
                distance = Levenshtein.distance(source_word.lower(), candidate.lower())
                traps.append((candidate, "Sound-alike", distance))
                self.stats["phonetic"] += 1
        
        return traps
    
    def _filter_semantic(self, session, source_word: str) -> List[Tuple[str, str, int]]:
        """
        Filter C: Find existing RELATED_TO relationships and flag as semantic traps.
        
        These are words that are related but commonly confused (e.g., affect/effect).
        
        Returns:
            List of (trap_word, reason, distance) tuples
        """
        traps = []
        
        result = session.run("""
            MATCH (source:Word {name: $source})-[:RELATED_TO]->(target:Word)
            WHERE target.frequency_rank <= $max_rank
            RETURN target.name as word
        """, source=source_word, max_rank=self.max_rank)
        
        for record in result:
            trap_word = record["word"]
            # Calculate Levenshtein distance for consistency
            distance = Levenshtein.distance(source_word.lower(), trap_word.lower())
            traps.append((trap_word, "Semantic", distance))
            self.stats["semantic"] += 1
        
        return traps
    
    def _combine_traps(self, 
                      morphology: List[Tuple[str, str, int]],
                      phonetic: List[Tuple[str, str, int]],
                      semantic: List[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
        """
        Combine trap lists and deduplicate.
        
        Priority: Morphology > Phonetic > Semantic
        (If a word appears in multiple filters, use the first reason)
        
        Returns:
            Deduplicated list of (trap_word, reason, distance) tuples
        """
        seen = set()
        combined = []
        
        # Add in priority order
        for trap_list in [morphology, phonetic, semantic]:
            for trap_word, reason, distance in trap_list:
                if trap_word not in seen:
                    seen.add(trap_word)
                    combined.append((trap_word, reason, distance))
        
        return combined
    
    def _create_confused_with_relationship(self, session, source: str, target: str, reason: str, distance: int):
        """
        Create a CONFUSED_WITH relationship in Neo4j.
        
        Args:
            session: Neo4j session
            source: Source word name
            target: Target word name
            reason: Reason for confusion ("Look-alike", "Sound-alike", "Semantic")
            distance: Levenshtein distance (or 0 for semantic)
        """
        # Create bidirectional relationship (words can confuse each other)
        query = """
        MATCH (source:Word {name: $source})
        MATCH (target:Word {name: $target})
        MERGE (source)-[r:CONFUSED_WITH]->(target)
        SET r.reason = $reason,
            r.distance = $distance,
            r.source = 'adversary_builder_v7.1'
        RETURN count(r) as created
        """
        
        result = session.run(query, source=source, target=target, reason=reason, distance=distance)
        
        if result.single()["created"] > 0:
            self.stats["total"] += 1
    
    def _print_summary(self, dry_run: bool):
        """Print summary statistics."""
        print(f"\n{'='*60}")
        print(f"✅ Adversary Builder Complete ({'DRY RUN' if dry_run else 'LIVE'})")
        print(f"{'='*60}")
        print(f"📊 Statistics:")
        print(f"   Morphology (Look-alike): {self.stats['morphology']}")
        print(f"   Phonetic (Sound-alike):  {self.stats['phonetic']}")
        print(f"   Semantic (Related):      {self.stats['semantic']}")
        print(f"   Total Relationships:     {self.stats['total']}")
        print(f"{'='*60}\n")


def run_adversary_builder(max_rank: int = 4000, dry_run: bool = False):
    """
    Main entry point for the Adversary Builder.
    
    Args:
        max_rank: Maximum frequency rank to process (default: 4000)
        dry_run: If True, only report what would be created
    """
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            builder = AdversaryBuilder(conn, max_rank=max_rank)
            builder.run(dry_run=dry_run)
        else:
            print("❌ Failed to connect to Neo4j")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    max_rank = 4000
    dry_run = False
    
    if len(sys.argv) > 1:
        max_rank = int(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "--dry-run":
        dry_run = True
    
    print(f"🚀 Starting Adversary Builder...")
    print(f"   Max Rank: {max_rank}")
    print(f"   Dry Run: {dry_run}\n")
    
    run_adversary_builder(max_rank=max_rank, dry_run=dry_run)

