"""
Analyze path lengths between Word nodes in Neo4j.

Answers: "How many hops on average for any given word reaching all other words?"
"""

import sys
import os
from pathlib import Path
from neo4j import GraphDatabase
from typing import Optional
from dotenv import load_dotenv
from collections import defaultdict
import statistics

load_dotenv()

class Neo4jConnection:
    """Manages Neo4j database connection and sessions."""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError(
                "Neo4j connection parameters missing. "
                "Provide uri/user/password or set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables."
            )
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def get_session(self):
        return self.driver.session()
    
    def verify_connectivity(self) -> bool:
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 as test")
                value = result.single()["test"]
                return value == 1
        except Exception as e:
            print(f"Connection verification failed: {e}")
            return False

def analyze_word_to_word_paths(conn: Neo4jConnection):
    """Analyze average hops from any word to all other words."""
    print("=" * 70)
    print("WORD-TO-WORD PATH LENGTH ANALYSIS")
    print("=" * 70)
    
    with conn.get_session() as session:
        # Get total word count
        total_words = session.run("MATCH (w:Word) RETURN count(w) as total").single()["total"]
        print(f"\nTotal Word nodes: {total_words:,}\n")
        
        # First, check connectivity - are all words reachable?
        print("Checking graph connectivity...")
        connectivity_query = """
        MATCH (w:Word)
        WITH collect(w) as words
        UNWIND words as w1
        WITH w1, words
        WHERE w1 IN words[0..10]  // Sample first 10 words
        MATCH path = shortestPath((w1)-[:RELATED_TO|OPPOSITE_TO*1..10]-(w2:Word))
        WHERE w1 <> w2
        WITH w1, count(DISTINCT w2) as reachable
        RETURN w1.name as word, reachable, (reachable * 100.0 / ($total - 1)) as percentage
        ORDER BY percentage DESC
        """
        
        result = session.run(connectivity_query, total=total_words)
        print("\nSample Connectivity (first 10 words):")
        print(f"{'Word':20} | Reachable | % Reachable")
        print("-" * 50)
        for record in result:
            print(f"{record['word']:20} | {record['reachable']:9} | {record['percentage']:10.1f}%")
        
        # Now analyze path lengths for ALL words
        print("\n" + "=" * 70)
        print("Calculating average path lengths for ALL words...")
        print("(This may take a minute for 3,500 words)")
        print("=" * 70)
        
        path_query = """
        MATCH (start:Word)
        MATCH path = shortestPath((start)-[:RELATED_TO|OPPOSITE_TO*1..10]-(target:Word))
        WHERE start <> target
        WITH start, target, length(path) as path_length
        WITH start, 
             count(DISTINCT target) as reachable_count,
             avg(path_length) as avg_hops,
             min(path_length) as min_hops,
             max(path_length) as max_hops,
             percentileCont(path_length, 0.5) as median_hops,
             percentileCont(path_length, 0.9) as p90_hops
        RETURN 
            start.name as word,
            start.frequency_rank as rank,
            reachable_count,
            (reachable_count * 100.0 / ($total - 1)) as reachable_percentage,
            avg_hops,
            min_hops,
            max_hops,
            median_hops,
            p90_hops
        ORDER BY avg_hops, reachable_percentage DESC
        """
        
        result = session.run(path_query, total=total_words)
        
        all_stats = []
        print(f"\n{'Word':20} | Rank | Reachable | % Reach | Avg Hops | Min | Max | Median | P90")
        print("-" * 90)
        
        for record in result:
            stats = {
                'word': record['word'],
                'rank': record['rank'],
                'reachable': record['reachable_count'],
                'percentage': record['reachable_percentage'],
                'avg_hops': record['avg_hops'],
                'min_hops': record['min_hops'],
                'max_hops': record['max_hops'],
                'median_hops': record['median_hops'],
                'p90_hops': record['p90_hops']
            }
            all_stats.append(stats)
            
            # Print top 20 and bottom 20
            if len(all_stats) <= 20 or len(all_stats) > total_words - 20:
                print(f"{stats['word']:20} | {stats['rank']:4} | {stats['reachable']:9} | {stats['percentage']:7.1f}% | {stats['avg_hops']:8.2f} | {stats['min_hops']:3} | {stats['max_hops']:3} | {stats['median_hops']:6.1f} | {stats['p90_hops']:4.1f}")
        
        if len(all_stats) > 40:
            print(f"\n... ({total_words - 40} words in between) ...\n")
        
        # Overall statistics
        print("\n" + "=" * 70)
        print("OVERALL STATISTICS")
        print("=" * 70)
        
        avg_hops_list = [s['avg_hops'] for s in all_stats if s['avg_hops'] is not None]
        reachable_pct_list = [s['percentage'] for s in all_stats]
        
        print(f"\nAverage Hops (across all words):")
        print(f"  Mean:   {statistics.mean(avg_hops_list):.2f} hops")
        print(f"  Median: {statistics.median(avg_hops_list):.2f} hops")
        print(f"  Min:    {min(avg_hops_list):.2f} hops")
        print(f"  Max:    {max(avg_hops_list):.2f} hops")
        print(f"  90th percentile: {statistics.quantiles(avg_hops_list, n=10)[8]:.2f} hops")
        
        print(f"\nReachability (across all words):")
        print(f"  Mean % reachable:   {statistics.mean(reachable_pct_list):.1f}%")
        print(f"  Median % reachable: {statistics.median(reachable_pct_list):.1f}%")
        print(f"  Min % reachable:    {min(reachable_pct_list):.1f}%")
        print(f"  Max % reachable:    {max(reachable_pct_list):.1f}%")
        
        # Path length distribution
        print("\n" + "=" * 70)
        print("PATH LENGTH DISTRIBUTION")
        print("=" * 70)
        
        # Get distribution of path lengths
        dist_query = """
        MATCH (start:Word)
        MATCH path = shortestPath((start)-[:RELATED_TO|OPPOSITE_TO*1..10]-(target:Word))
        WHERE start <> target
        WITH length(path) as hops
        WITH hops, count(*) as count
        RETURN hops, count
        ORDER BY hops
        """
        
        result = session.run(dist_query)
        print(f"\n{'Hops':6} | Count")
        print("-" * 20)
        total_paths = 0
        for record in result:
            hops = record['hops']
            count = record['count']
            total_paths += count
            print(f"{hops:6} | {count:,}")
        
        print(f"\nTotal paths analyzed: {total_paths:,}")
        
        # Answer the key question
        print("\n" + "=" * 70)
        print("ANSWER TO THE QUESTION")
        print("=" * 70)
        print(f"\n🎯 On average, it takes {statistics.mean(avg_hops_list):.2f} hops")
        print(f"   for any given word to reach all other reachable words.")
        print(f"\n📊 Additional insights:")
        print(f"   - Median: {statistics.median(avg_hops_list):.2f} hops")
        print(f"   - Words can reach {statistics.mean(reachable_pct_list):.1f}% of other words on average")
        print(f"   - Path lengths range from {min([s['min_hops'] for s in all_stats if s['min_hops']]):.0f} to {max([s['max_hops'] for s in all_stats if s['max_hops']]):.0f} hops")


if __name__ == "__main__":
    conn = Neo4jConnection()
    
    try:
        if not conn.verify_connectivity():
            print("❌ Failed to connect to Neo4j")
            exit(1)
        
        print("✅ Connected to Neo4j\n")
        
        analyze_word_to_word_paths(conn)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

