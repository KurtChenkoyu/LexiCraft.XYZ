"""
Mine Service

Handles block discovery and exploration in The Mine (Neo4j knowledge graph).
Provides starter pack for new users and personalized blocks for surveyed users.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
import random

from ..database.neo4j_connection import Neo4jConnection
from .levels import LevelService


class MineService:
    """Service for exploring The Mine and discovering blocks."""
    
    def __init__(self, db: Session, neo4j: Optional[Neo4jConnection] = None):
        self.db = db
        self.neo4j = neo4j or Neo4jConnection()
        self.level_service = LevelService(db)
    
    def has_completed_survey(self, user_id: UUID) -> bool:
        """
        Check if user has completed a survey.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user has completed survey, False otherwise
        """
        result = self.db.execute(
            text("""
                SELECT COUNT(*) 
                FROM survey_sessions ss
                JOIN survey_results sr ON sr.session_id = ss.id
                WHERE ss.user_id = :user_id
                AND ss.status = 'completed'
            """),
            {'user_id': user_id}
        )
        count = result.scalar() or 0
        return count > 0
    
    def get_starter_pack(self, limit: int = 50) -> List[Dict]:
        """
        Get curated starter pack of blocks across frequency bands.
        
        For users without survey - shows diverse blocks to explore.
        
        Args:
            limit: Total number of blocks to return
            
        Returns:
            List of block dictionaries with sense_id, word, tier, etc.
        """
        try:
            with self.neo4j.get_session() as session:
                # Sample from each frequency band
                bands = [
                    (1, 500, 10),      # 10 blocks from top 500
                    (501, 1000, 10),   # 10 from 501-1000
                    (1001, 2000, 15),  # 15 from 1001-2000
                    (2001, 3500, 15),  # 15 from 2001-3500
                ]
                
                all_blocks = []
                
                for min_rank, max_rank, count in bands:
                    # Try enriched first, fall back to all if not enough
                    query = """
                        MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                        WHERE w.frequency_rank >= $min_rank 
                        AND w.frequency_rank <= $max_rank
                        AND (s.enriched = true OR s.enriched IS NULL)
                        WITH w, s, rand() as r
                        ORDER BY r
                        LIMIT $count
                        RETURN 
                            s.id as sense_id,
                            w.name as word,
                            COALESCE(s.definition_en, s.definition, '') as definition_preview,
                            COALESCE(s.definition_zh_translation, s.definition_zh, '') as definition_zh,
                            w.frequency_rank as rank,
                            1 as tier
                    """
                    
                    try:
                        result = session.run(
                            query,
                            min_rank=min_rank,
                            max_rank=max_rank,
                            count=count
                        )
                        
                        for record in result:
                            all_blocks.append({
                                'sense_id': record['sense_id'],
                                'word': record['word'],
                                'definition_preview': (record['definition_preview'] or '')[:100] if record.get('definition_preview') else '',
                                'definition_zh': record.get('definition_zh') or '',
                                'rank': record['rank'],
                                'tier': record['tier'],
                            })
                    except Exception as e:
                        print(f"Warning: Failed to fetch blocks for band {min_rank}-{max_rank}: {e}")
                        continue
                
                # Shuffle and limit
                random.shuffle(all_blocks)
                return all_blocks[:limit]
        except Exception as e:
            print(f"Error in get_starter_pack: {e}")
            import traceback
            traceback.print_exc()
            # Return empty list on error - better than crashing
            return []
    
    def get_personalized_blocks(self, user_id: UUID, limit: int = 50) -> Tuple[List[Dict], Dict]:
        """
        Get personalized blocks for surveyed users.
        
        Returns:
            - Blocks they missed (knowledge gaps)
            - Prerequisites of what they know
            - Connected blocks (RELATED_TO, OPPOSITE_TO)
            
        Args:
            user_id: User ID
            limit: Total number of blocks to return
            
        Returns:
            Tuple of (blocks list, stats dict with gaps_count, prerequisites_count)
        """
        # 1. Get survey results - find missed words
        missed_sense_ids = self._get_missed_words_from_survey(user_id)
        
        # 2. Get user's known blocks
        known_sense_ids = self._get_user_known_blocks(user_id)
        
        # 3. Query Neo4j for missed blocks + prerequisites + connections
        try:
            with self.neo4j.get_session() as session:
                blocks = []
                gaps_count = len(missed_sense_ids)
                prerequisites_count = 0
                
                # Get missed blocks
                if missed_sense_ids:
                    query = """
                        MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
                        WHERE s.id IN $sense_ids
                        AND (s.enriched = true OR s.enriched IS NULL)
                        RETURN 
                            s.id as sense_id,
                            w.name as word,
                            COALESCE(s.definition_en, s.definition, '') as definition_preview,
                            COALESCE(s.definition_zh_translation, s.definition_zh, '') as definition_zh,
                            w.frequency_rank as rank,
                            1 as tier,
                            'gap' as source
                        LIMIT $limit
                    """
                    result = session.run(query, sense_ids=missed_sense_ids, limit=limit)
                    for record in result:
                        blocks.append({
                            'sense_id': record['sense_id'],
                            'word': record['word'],
                            'definition_preview': (record.get('definition_preview') or '')[:100],
                            'definition_zh': record.get('definition_zh') or '',
                            'rank': record['rank'],
                            'tier': record['tier'],
                            'source': record['source'],
                        })
                
                # Get prerequisites of known blocks (if PREREQUISITE_OF relationship exists)
                # Note: This relationship may not exist in current schema, so we'll skip if no results
                if known_sense_ids and len(blocks) < limit:
                    # Try to find related words first, then get their senses
                    query = """
                        MATCH (known:Sense)<-[:HAS_SENSE]-(known_word:Word)
                        WHERE known.id IN $known_ids
                        OPTIONAL MATCH (known_word)-[:RELATED_TO|OPPOSITE_TO]-(related_word:Word)
                        WHERE related_word IS NOT NULL
                        MATCH (related_word)-[:HAS_SENSE]->(related_sense:Sense)
                        WHERE (related_sense.enriched = true OR related_sense.enriched IS NULL)
                        AND NOT related_sense.id IN $known_ids
                        RETURN DISTINCT
                            related_sense.id as sense_id,
                            related_word.name as word,
                            COALESCE(related_sense.definition_en, related_sense.definition, '') as definition_preview,
                            COALESCE(related_sense.definition_zh_translation, related_sense.definition_zh, '') as definition_zh,
                            related_word.frequency_rank as rank,
                            1 as tier,
                            'prerequisite' as source
                        LIMIT $remaining
                    """
                    remaining = limit - len(blocks)
                    result = session.run(
                        query,
                        known_ids=known_sense_ids,
                        remaining=remaining
                    )
                    for record in result:
                        blocks.append({
                            'sense_id': record['sense_id'],
                            'word': record['word'],
                            'definition_preview': (record.get('definition_preview') or '')[:100],
                            'definition_zh': record.get('definition_zh') or '',
                            'rank': record['rank'],
                            'tier': record['tier'],
                            'source': record['source'],
                        })
                        prerequisites_count += 1
                
                # Get connected blocks via Word relationships (RELATED_TO, OPPOSITE_TO)
                if known_sense_ids and len(blocks) < limit:
                    query = """
                        MATCH (known:Sense)<-[:HAS_SENSE]-(known_word:Word)
                        WHERE known.id IN $known_ids
                        MATCH (known_word)-[r:RELATED_TO|OPPOSITE_TO]-(connected_word:Word)
                        MATCH (connected_word)-[:HAS_SENSE]->(connected_sense:Sense)
                        WHERE (connected_sense.enriched = true OR connected_sense.enriched IS NULL)
                        AND NOT connected_sense.id IN $known_ids
                        RETURN DISTINCT
                            connected_sense.id as sense_id,
                            connected_word.name as word,
                            COALESCE(connected_sense.definition_en, connected_sense.definition, '') as definition_preview,
                            COALESCE(connected_sense.definition_zh_translation, connected_sense.definition_zh, '') as definition_zh,
                            connected_word.frequency_rank as rank,
                            1 as tier,
                            type(r) as source
                        LIMIT $remaining
                    """
                    remaining = limit - len(blocks)
                    result = session.run(
                        query,
                        known_ids=known_sense_ids,
                        remaining=remaining
                    )
                    for record in result:
                        # Avoid duplicates
                        if not any(b['sense_id'] == record['sense_id'] for b in blocks):
                            blocks.append({
                                'sense_id': record['sense_id'],
                                'word': record['word'],
                                'definition_preview': (record['definition_preview'] or '')[:100] if record.get('definition_preview') else '',
                                'definition_zh': record.get('definition_zh'),
                                'rank': record['rank'],
                                'tier': record['tier'],
                                'source': record['source'].lower(),
                            })
                
                stats = {
                    'gaps_count': gaps_count,
                    'prerequisites_count': prerequisites_count,
                }
                
                return blocks[:limit], stats
        except Exception as e:
            print(f"Error in get_personalized_blocks: {e}")
            import traceback
            traceback.print_exc()
            # Return empty list on error
            return [], {'gaps_count': 0, 'prerequisites_count': 0}
    
    def get_block_detail(self, sense_id: str, user_id: UUID) -> Dict:
        """
        Get full block detail with connections and user progress.
        
        Args:
            sense_id: Neo4j Sense.id
            user_id: User ID
            
        Returns:
            Dictionary with full block information
        """
        try:
            with self.neo4j.get_session() as session:
                # Get block data with connections via Word relationships
                query = """
                    MATCH (w:Word)-[:HAS_SENSE]->(s:Sense {id: $sense_id})
                    OPTIONAL MATCH (w)-[r:RELATED_TO|OPPOSITE_TO]-(connected_word:Word)
                    OPTIONAL MATCH (connected_word)-[:HAS_SENSE]->(connected_sense:Sense)
                    WHERE connected_sense IS NOT NULL
                    RETURN 
                        s.id as sense_id,
                        w.name as word,
                        COALESCE(s.definition_en, s.definition, '') as definition_en,
                        COALESCE(s.definition_zh_translation, s.definition_zh, '') as definition_zh,
                        COALESCE(s.definition_zh_explanation, '') as definition_zh_explanation,
                        s.example_en as example_en,
                        COALESCE(s.example_zh_translation, s.example_zh, '') as example_zh,
                        COALESCE(s.example_zh_explanation, '') as example_zh_explanation,
                        w.frequency_rank as rank,
                        1 as tier,
                        collect(DISTINCT {
                            sense_id: connected_sense.id,
                            word: connected_word.name,
                            type: type(r)
                        }) as connections
                """
                
                result = session.run(query, sense_id=sense_id)
                record = result.single()
                
                if not record:
                    raise ValueError(f"Block not found: {sense_id}")
                
                # Get user progress
                user_progress = self._get_user_progress_for_block(user_id, sense_id)
                
                # Calculate dynamic value
                connection_count = len([c for c in record['connections'] if c.get('sense_id')])
                total_value = self.calculate_block_value(sense_id, record['tier'], connection_count)
                
                return {
                    'sense_id': record['sense_id'],
                    'word': record['word'],
                    'tier': record['tier'],
                    'base_xp': self.level_service.TIER_BASE_XP.get(record['tier'], 100),
                    'connection_count': connection_count,
                    'total_value': total_value,
                    'rank': record['rank'],
                    'definition_en': record.get('definition_en') or '',
                    'definition_zh': (record.get('definition_zh') or '') + ((' ' + record.get('definition_zh_explanation')) if record.get('definition_zh_explanation') else ''),
                    'example_en': record.get('example_en') or '',
                    'example_zh': (record.get('example_zh') or '') + ((' ' + record.get('example_zh_explanation')) if record.get('example_zh_explanation') else ''),
                    'connections': [
                        {
                            'sense_id': c.get('sense_id'),
                            'word': c.get('word'),
                            'type': c.get('type'),
                        }
                        for c in record['connections'] if c.get('sense_id')
                    ],
                    'user_progress': user_progress,
                }
        except Exception as e:
            print(f"Error in get_block_detail for {sense_id}: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to get block detail: {str(e)}")
    
    def calculate_block_value(self, sense_id: str, tier: int, connection_count: int) -> int:
        """
        Calculate dynamic block value (base XP + connection bonus).
        
        Args:
            sense_id: Neo4j Sense.id (for future connection querying)
            tier: Block tier (1-7)
            connection_count: Number of connections
            
        Returns:
            Total XP value
        """
        base_xp = self.level_service.TIER_BASE_XP.get(tier, 100)
        
        # Connection bonus (average 10 XP per connection)
        connection_bonus = connection_count * 10
        
        return base_xp + connection_bonus
    
    def _get_missed_words_from_survey(self, user_id: UUID) -> List[str]:
        """
        Get sense_ids of words user missed in survey.
        
        Args:
            user_id: User ID
            
        Returns:
            List of sense_ids that were answered incorrectly
        """
        result = self.db.execute(
            text("""
                SELECT sh.history
                FROM survey_sessions ss
                JOIN survey_history sh ON sh.session_id = ss.id
                WHERE ss.user_id = :user_id
                AND ss.status = 'completed'
                ORDER BY ss.start_time DESC
                LIMIT 1
            """),
            {'user_id': user_id}
        )
        
        row = result.fetchone()
        if not row or not row[0]:
            return []
        
        history = row[0]  # JSONB array
        missed = []
        
        for entry in history:
            if isinstance(entry, dict) and entry.get('correct') is False:
                sense_id = entry.get('sense_id')
                if sense_id:
                    missed.append(sense_id)
        
        return missed
    
    def _get_user_known_blocks(self, user_id: UUID) -> List[str]:
        """
        Get sense_ids of blocks user has verified.
        
        Args:
            user_id: User ID
            
        Returns:
            List of sense_ids (learning_point_id values)
        """
        result = self.db.execute(
            text("""
                SELECT learning_point_id
                FROM learning_progress
                WHERE user_id = :user_id
                AND status = 'verified'
            """),
            {'user_id': user_id}
        )
        
        return [row[0] for row in result.fetchall()]
    
    def _get_user_progress_for_block(self, user_id: UUID, sense_id: str) -> Optional[Dict]:
        """
        Get user's progress for a specific block.
        
        Args:
            user_id: User ID
            sense_id: Neo4j Sense.id (learning_point_id)
            
        Returns:
            Dictionary with progress info or None
        """
        result = self.db.execute(
            text("""
                SELECT 
                    id,
                    status,
                    tier,
                    learned_at
                FROM learning_progress
                WHERE user_id = :user_id
                AND learning_point_id = :sense_id
                ORDER BY learned_at DESC
                LIMIT 1
            """),
            {'user_id': user_id, 'sense_id': sense_id}
        )
        
        row = result.fetchone()
        if not row:
            return None
        
        status = row[1] or 'pending'
        mastery = 'mastered' if status == 'verified' else status
        
        return {
            'status': status,
            'tier': row[2],
            'started_at': row[3].isoformat() if row[3] else None,
            'mastery_level': mastery,
        }
    
    def enrich_blocks_with_user_status(self, blocks: List[Dict], user_id: UUID) -> List[Dict]:
        """
        Enrich blocks with user progress status (raw/hollow/solid).
        
        Args:
            blocks: List of block dictionaries with sense_id
            user_id: User ID
            
        Returns:
            Enriched blocks with status field
        """
        if not blocks:
            return []
        
        sense_ids = [b['sense_id'] for b in blocks]
        
        # Get user progress for these blocks
        # Note: Using just learning_progress.status for now (simplified schema)
        result = self.db.execute(
            text("""
                SELECT 
                    learning_point_id,
                    status
                FROM learning_progress
                WHERE user_id = :user_id
                AND learning_point_id = ANY(:sense_ids)
            """),
            {'user_id': user_id, 'sense_ids': sense_ids}
        )
        
        # Create lookup
        progress_map = {}
        for row in result.fetchall():
            sense_id = row[0]
            status = row[1]
            
            # Determine block state based on status
            # 'verified' or 'mastered' = solid, 'learning'/'pending' = hollow, else raw
            if status in ('verified', 'mastered'):
                block_status = 'solid'
            elif status in ('learning', 'pending'):
                block_status = 'hollow'
            else:
                block_status = 'raw'
            
            progress_map[sense_id] = block_status
        
        # Enrich blocks
        for block in blocks:
            block['status'] = progress_map.get(block['sense_id'], 'raw')
            # Calculate dynamic value
            # Note: connection_count not calculated yet for list views (performance)
            # Will be calculated when viewing block detail
            connection_count = block.get('connection_count', 0)
            tier = block.get('tier', 1)
            base_xp = self.level_service.TIER_BASE_XP.get(tier, 100)
            block['base_xp'] = base_xp
            block['connection_count'] = connection_count
            # For now, use base_xp as total_value (connection bonus calculated on detail view)
            block['total_value'] = base_xp + (connection_count * 10)
        
        return blocks
    
    def process_mining_batch(
        self,
        user_id: UUID,
        sense_ids: List[str],
        tier: int = 1
    ) -> Dict:
        """
        Process a batch of mined blocks (Phase 5b - Backend Persistence).
        
        Creates learning progress entries and awards points.
        
        Args:
            user_id: User ID
            sense_ids: List of sense IDs that were mined
            tier: Tier for all blocks (default 1)
            
        Returns:
            Dictionary with:
                - success: bool
                - mined_count: int (how many were newly added)
                - skipped_count: int (how many already existed)
                - new_wallet_balance: dict
                - xp_gained: int
        """
        try:
            from ..database.postgres_crud.progress import (
                create_learning_progress,
                get_learning_progress_by_learning_point
            )
            from ..database.postgres_crud.points import (
                get_points_account,
                create_points_transaction
            )
            
            # Track newly mined vs already in inventory
            mined_count = 0
            skipped_count = 0
            
            for sense_id in sense_ids:
                # Check if already exists
                existing = get_learning_progress_by_learning_point(
                    self.db,
                    user_id,
                    sense_id,
                    tier
                )
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new learning progress entry
                create_learning_progress(
                    self.db,
                    user_id=user_id,
                    learning_point_id=sense_id,
                    tier=tier,
                    status='learning'
                )
                mined_count += 1
            
            # Award points (10 XP per newly mined word)
            xp_gained = mined_count * 10
            
            if xp_gained > 0:
                # Get or create points account
                points_account = get_points_account(self.db, user_id)
                if not points_account:
                    # Create initial points account
                    from ..database.models import PointsAccount
                    points_account = PointsAccount(
                        user_id=user_id,
                        total_earned=0,
                        available_points=0,
                        locked_points=0,
                        withdrawn_points=0
                    )
                    self.db.add(points_account)
                    self.db.commit()
                    self.db.refresh(points_account)
                
                # Create transaction
                create_points_transaction(
                    self.db,
                    user_id=user_id,
                    transaction_type='earned',
                    points=xp_gained,
                    tier=tier,
                    description=f'Mined {mined_count} words'
                )
                
                # Update account balance
                points_account.total_earned += xp_gained
                points_account.available_points += xp_gained
                self.db.commit()
                self.db.refresh(points_account)
                
                new_wallet = {
                    'total_earned': points_account.total_earned,
                    'available_points': points_account.available_points,
                    'locked_points': points_account.locked_points,
                    'withdrawn_points': points_account.withdrawn_points,
                }
            else:
                # No points gained, return current balance
                points_account = get_points_account(self.db, user_id)
                if points_account:
                    new_wallet = {
                        'total_earned': points_account.total_earned,
                        'available_points': points_account.available_points,
                        'locked_points': points_account.locked_points,
                        'withdrawn_points': points_account.withdrawn_points,
                    }
                else:
                    new_wallet = {
                        'total_earned': 0,
                        'available_points': 0,
                        'locked_points': 0,
                        'withdrawn_points': 0,
                    }
            
            return {
                'success': True,
                'mined_count': mined_count,
                'skipped_count': skipped_count,
                'new_wallet_balance': new_wallet,
                'xp_gained': xp_gained,
            }
            
        except Exception as e:
            print(f"Error in process_mining_batch: {e}")
            import traceback
            traceback.print_exc()
            # Rollback on error
            self.db.rollback()
            raise ValueError(f"Failed to process mining batch: {str(e)}")

