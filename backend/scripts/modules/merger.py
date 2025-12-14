"""
Data Merger - Intelligent merging of all three enrichment layers

Combines:
- Layer 1: Deep WordNet relationships
- Layer 2: Free Dictionary API common synonyms/antonyms
- Layer 3: Cascading collocations (NGSL → WordNet → Datamuse)

Priority: base → WordNet → Free Dict → Collocations
"""

import threading
from typing import Dict, List


class DataMerger:
    """Merges data from all enrichment layers."""
    
    def __init__(self):
        """Initialize merger."""
        self.stats = {
            'total_merged': 0,
            'connections_added': 0,
            'collocations_added': 0,
        }
        self.stats_lock = threading.Lock()  # Thread-safe stats
    
    def merge_layers(
        self,
        base_sense: Dict,
        wordnet_data: Dict,
        free_dict_data: Dict,
        collocations: Dict
    ) -> Dict:
        """
        Intelligent merge of all three data sources.
        
        Args:
            base_sense: Original sense data from vocabulary.json
            wordnet_data: Deep WordNet relationships
            free_dict_data: Connections dict updated with Free Dict data
            collocations: Collocation data from cascade
        
        Returns:
            Merged sense data
        """
        with self.stats_lock:
            self.stats['total_merged'] += 1
        
        # Start with base sense
        merged = base_sense.copy()
        
        # Ensure connections dict exists
        if 'connections' not in merged:
            merged['connections'] = {}
        
        # 1. Merge WordNet relationships (high confidence)
        connection_types = [
            'related', 'opposite',  # Existing
            'derivations', 'similar', 'attributes',  # New from WordNet
            'also_sees', 'entailments', 'causes'
        ]
        
        for conn_type in connection_types:
            if conn_type in wordnet_data and wordnet_data[conn_type]:
                # For existing types (related, opposite), merge with existing data
                if conn_type in ['related', 'opposite']:
                    existing = merged['connections'].get(conn_type, [])
                    new_values = wordnet_data[conn_type]
                    # Combine and deduplicate (handle both lists properly)
                    combined = existing + [v for v in new_values if v not in existing]
                    merged['connections'][conn_type] = combined
                else:
                    # New types, just add them
                    merged['connections'][conn_type] = wordnet_data[conn_type]
                
                with self.stats_lock:
                    self.stats['connections_added'] += len(wordnet_data[conn_type])
        
        # Handle morphological forms (dict, not list)
        if 'morphological' in wordnet_data and wordnet_data['morphological']:
            merged['connections']['morphological'] = wordnet_data['morphological']
            total_morph = sum(len(v) for v in wordnet_data['morphological'].values())
            with self.stats_lock:
                self.stats['connections_added'] += total_morph
        
        # Preserve confused connections (they're objects, not sense IDs)
        if 'confused' in merged['connections']:
            # Keep confused as-is, it has a different structure
            pass
        
        # 2. Free Dict data is already merged into free_dict_data connections
        # Update the merged connections with free_dict augmented data
        if 'related' in free_dict_data:
            merged['connections']['related'] = free_dict_data['related']
        if 'opposite' in free_dict_data:
            merged['connections']['opposite'] = free_dict_data['opposite']
        
        # 3. Add collocations to connections.phrases
        if collocations and collocations.get('all_phrases'):
            # Use existing 'phrases' field in connections
            merged['connections']['phrases'] = collocations['all_phrases']
            # Optionally store source breakdown as metadata
            if 'collocation_sources' not in merged:
                merged['collocation_sources'] = collocations.get('source_breakdown', {})
            with self.stats_lock:
                self.stats['collocations_added'] += len(collocations['all_phrases'])
        
        # 4. Calculate connection counts
        total_connections = 0
        for conn_type, conn_list in merged['connections'].items():
            if isinstance(conn_list, list):
                total_connections += len(conn_list)
        
        if 'connection_counts' not in merged:
            merged['connection_counts'] = {}
        merged['connection_counts']['total'] = total_connections
        
        # 5. Update enrichment metadata
        merged['enriched'] = True
        merged['enrichment_stage'] = 3
        
        return merged
    
    def get_stats(self) -> Dict:
        """Get merger statistics."""
        return self.stats.copy()

