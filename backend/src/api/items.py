"""
Items API

Endpoints for building items (furniture) in rooms.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.postgres_connection import PostgresConnection
from ..middleware.auth import get_current_user_id
from ..services.currencies import CurrencyService

router = APIRouter(prefix="/api/v1/items", tags=["Items"])


# --- Response Models ---

class ItemBlueprint(BaseModel):
    """Item blueprint definition."""
    id: str
    code: str
    name_en: str
    name_zh: Optional[str]
    room: str
    max_level: int
    emoji_levels: List[str]
    is_starter: bool
    display_order: int


class UserItem(BaseModel):
    """User's item with current level."""
    blueprint: ItemBlueprint
    current_level: int
    current_emoji: str
    next_level: Optional[int]
    next_emoji: Optional[str]
    upgrade_cost: Optional[Dict[str, int]]  # {energy, essence, blocks}
    can_upgrade: bool
    upgraded_at: Optional[str]


class RoomItems(BaseModel):
    """All items in a room."""
    room: str
    room_name_en: str
    room_name_zh: str
    items: List[UserItem]


class UpgradeRequest(BaseModel):
    """Request to upgrade an item."""
    item_code: str


class UpgradeResponse(BaseModel):
    """Response after upgrading an item."""
    success: bool
    error: Optional[str]
    item_code: str
    old_level: int
    new_level: int
    new_emoji: str
    energy_spent: int
    essence_spent: int
    blocks_spent: int
    currencies_after: Dict[str, int]


# --- Dependency Injection ---

def get_db_session():
    """Get database session."""
    conn = PostgresConnection()
    return conn.get_session()


# --- Endpoints ---

@router.get("/blueprints", response_model=List[ItemBlueprint])
async def get_blueprints(
    room: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """
    Get all item blueprints.
    
    Args:
        room: Filter by room ('study' or 'living')
    """
    try:
        query = """
            SELECT id, code, name_en, name_zh, room, max_level, 
                   emoji_levels, is_starter, display_order
            FROM item_blueprints
        """
        params = {}
        
        if room:
            query += " WHERE room = :room"
            params['room'] = room
        
        query += " ORDER BY room, display_order"
        
        result = db.execute(text(query), params)
        
        blueprints = []
        for row in result.fetchall():
            blueprints.append(ItemBlueprint(
                id=str(row[0]),
                code=row[1],
                name_en=row[2],
                name_zh=row[3],
                room=row[4],
                max_level=row[5],
                emoji_levels=row[6] or [],
                is_starter=row[7] or False,
                display_order=row[8] or 0
            ))
        
        return blueprints
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blueprints: {str(e)}")
    finally:
        db.close()


@router.get("/rooms", response_model=List[RoomItems])
async def get_rooms(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get all rooms with user's items and upgrade status.
    
    Returns study room and living room with all items and their current levels.
    """
    try:
        # Initialize user items if needed
        db.execute(text("SELECT initialize_user_items(:user_id)"), {'user_id': user_id})
        db.commit()
        
        # Get user currencies for "can afford" check
        currency_service = CurrencyService(db)
        currencies = currency_service.get_currencies(user_id)
        
        # Get all blueprints with user levels
        result = db.execute(
            text("""
                SELECT b.id, b.code, b.name_en, b.name_zh, b.room, b.max_level,
                       b.emoji_levels, b.is_starter, b.display_order,
                       b.upgrade_energy, b.upgrade_essence, b.upgrade_blocks,
                       COALESCE(ui.current_level, 0) as current_level,
                       ui.upgraded_at
                FROM item_blueprints b
                LEFT JOIN user_items ui ON b.id = ui.blueprint_id AND ui.user_id = :user_id
                ORDER BY b.room, b.display_order
            """),
            {'user_id': user_id}
        )
        
        rooms_data = {
            'study': {'name_en': 'Study Room', 'name_zh': '書房', 'items': []},
            'living': {'name_en': 'Living Room', 'name_zh': '客廳', 'items': []}
        }
        
        for row in result.fetchall():
            room = row[4]
            if room not in rooms_data:
                continue
            
            current_level = row[12] or 0
            max_level = row[5]
            emoji_levels = row[6] or []
            upgrade_energy = row[9] or []
            upgrade_essence = row[10] or []
            upgrade_blocks = row[11] or []
            
            # Current emoji (handle level 0 = broken state)
            current_emoji = emoji_levels[current_level] if current_level < len(emoji_levels) else emoji_levels[-1] if emoji_levels else '❓'
            
            # Next level info
            can_level_up = current_level < max_level
            next_level = current_level + 1 if can_level_up else None
            next_emoji = emoji_levels[next_level] if next_level and next_level < len(emoji_levels) else None
            
            # Upgrade cost (array index = level, so index 0 = cost for L0→L1)
            upgrade_cost = None
            can_upgrade = False
            if can_level_up and current_level < len(upgrade_energy):
                energy_cost = upgrade_energy[current_level] if current_level < len(upgrade_energy) else 0
                essence_cost = upgrade_essence[current_level] if current_level < len(upgrade_essence) else 0
                blocks_cost = upgrade_blocks[current_level] if current_level < len(upgrade_blocks) else 0
                
                upgrade_cost = {
                    'energy': energy_cost,
                    'essence': essence_cost,
                    'blocks': blocks_cost
                }
                
                can_upgrade = (
                    currencies['energy'] >= energy_cost and
                    currencies['essence'] >= essence_cost and
                    currencies['blocks'] >= blocks_cost
                )
            
            blueprint = ItemBlueprint(
                id=str(row[0]),
                code=row[1],
                name_en=row[2],
                name_zh=row[3],
                room=room,
                max_level=max_level,
                emoji_levels=emoji_levels,
                is_starter=row[7] or False,
                display_order=row[8] or 0
            )
            
            user_item = UserItem(
                blueprint=blueprint,
                current_level=current_level,
                current_emoji=current_emoji,
                next_level=next_level,
                next_emoji=next_emoji,
                upgrade_cost=upgrade_cost,
                can_upgrade=can_upgrade,
                upgraded_at=row[13].isoformat() if row[13] else None
            )
            
            rooms_data[room]['items'].append(user_item)
        
        return [
            RoomItems(
                room='study',
                room_name_en=rooms_data['study']['name_en'],
                room_name_zh=rooms_data['study']['name_zh'],
                items=rooms_data['study']['items']
            ),
            RoomItems(
                room='living',
                room_name_en=rooms_data['living']['name_en'],
                room_name_zh=rooms_data['living']['name_zh'],
                items=rooms_data['living']['items']
            )
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rooms: {str(e)}")
    finally:
        db.close()


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_item(
    request: UpgradeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Upgrade an item to the next level.
    
    Deducts the required Energy, Essence, and Blocks from user's balance.
    """
    try:
        # Get blueprint
        result = db.execute(
            text("""
                SELECT id, max_level, emoji_levels, upgrade_energy, upgrade_essence, upgrade_blocks
                FROM item_blueprints
                WHERE code = :code
            """),
            {'code': request.item_code}
        )
        blueprint_row = result.fetchone()
        
        if not blueprint_row:
            raise HTTPException(status_code=404, detail=f"Item not found: {request.item_code}")
        
        blueprint_id = blueprint_row[0]
        max_level = blueprint_row[1]
        emoji_levels = blueprint_row[2] or []
        upgrade_energy = blueprint_row[3] or []
        upgrade_essence = blueprint_row[4] or []
        upgrade_blocks = blueprint_row[5] or []
        
        # Get or create user item
        result = db.execute(
            text("""
                SELECT current_level FROM user_items
                WHERE user_id = :user_id AND blueprint_id = :blueprint_id
            """),
            {'user_id': user_id, 'blueprint_id': blueprint_id}
        )
        item_row = result.fetchone()
        
        if not item_row:
            # Create item at level 0
            db.execute(
                text("""
                    INSERT INTO user_items (user_id, blueprint_id, current_level)
                    VALUES (:user_id, :blueprint_id, 0)
                """),
                {'user_id': user_id, 'blueprint_id': blueprint_id}
            )
            current_level = 0
        else:
            current_level = item_row[0] or 0
        
        # Check max level
        if current_level >= max_level:
            return UpgradeResponse(
                success=False,
                error="ALREADY_MAX_LEVEL",
                item_code=request.item_code,
                old_level=current_level,
                new_level=current_level,
                new_emoji=emoji_levels[current_level] if current_level < len(emoji_levels) else '❓',
                energy_spent=0,
                essence_spent=0,
                blocks_spent=0,
                currencies_after={}
            )
        
        # Get upgrade cost
        energy_cost = upgrade_energy[current_level] if current_level < len(upgrade_energy) else 0
        essence_cost = upgrade_essence[current_level] if current_level < len(upgrade_essence) else 0
        blocks_cost = upgrade_blocks[current_level] if current_level < len(upgrade_blocks) else 0
        
        # Spend currencies
        currency_service = CurrencyService(db)
        success, spend_result = currency_service.spend_currencies(
            user_id,
            energy=energy_cost,
            essence=essence_cost,
            blocks=blocks_cost,
            source='item_upgrade',
            source_id=blueprint_id,
            description=f'Upgrade {request.item_code} to L{current_level + 1}'
        )
        
        if not success:
            currencies = currency_service.get_currencies(user_id)
            return UpgradeResponse(
                success=False,
                error=spend_result.get('error', 'INSUFFICIENT_FUNDS'),
                item_code=request.item_code,
                old_level=current_level,
                new_level=current_level,
                new_emoji=emoji_levels[current_level] if current_level < len(emoji_levels) else '❓',
                energy_spent=0,
                essence_spent=0,
                blocks_spent=0,
                currencies_after={
                    'energy': currencies['energy'],
                    'essence': currencies['essence'],
                    'blocks': currencies['blocks']
                }
            )
        
        # Upgrade item
        new_level = current_level + 1
        db.execute(
            text("""
                UPDATE user_items
                SET current_level = :level, upgraded_at = NOW()
                WHERE user_id = :user_id AND blueprint_id = :blueprint_id
            """),
            {'user_id': user_id, 'blueprint_id': blueprint_id, 'level': new_level}
        )
        db.commit()
        
        new_emoji = emoji_levels[new_level] if new_level < len(emoji_levels) else emoji_levels[-1] if emoji_levels else '❓'
        
        return UpgradeResponse(
            success=True,
            error=None,
            item_code=request.item_code,
            old_level=current_level,
            new_level=new_level,
            new_emoji=new_emoji,
            energy_spent=energy_cost,
            essence_spent=essence_cost,
            blocks_spent=blocks_cost,
            currencies_after={
                'energy': spend_result.get('energy_after', 0),
                'essence': spend_result.get('essence_after', 0),
                'blocks': spend_result.get('blocks_after', 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upgrade item: {str(e)}")
    finally:
        db.close()


@router.get("/{item_code}", response_model=UserItem)
async def get_item(
    item_code: str,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """
    Get a specific item with user's progress.
    """
    try:
        currency_service = CurrencyService(db)
        currencies = currency_service.get_currencies(user_id)
        
        result = db.execute(
            text("""
                SELECT b.id, b.code, b.name_en, b.name_zh, b.room, b.max_level,
                       b.emoji_levels, b.is_starter, b.display_order,
                       b.upgrade_energy, b.upgrade_essence, b.upgrade_blocks,
                       COALESCE(ui.current_level, 0) as current_level,
                       ui.upgraded_at
                FROM item_blueprints b
                LEFT JOIN user_items ui ON b.id = ui.blueprint_id AND ui.user_id = :user_id
                WHERE b.code = :code
            """),
            {'user_id': user_id, 'code': item_code}
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Item not found: {item_code}")
        
        current_level = row[12] or 0
        max_level = row[5]
        emoji_levels = row[6] or []
        upgrade_energy = row[9] or []
        upgrade_essence = row[10] or []
        upgrade_blocks = row[11] or []
        
        current_emoji = emoji_levels[current_level] if current_level < len(emoji_levels) else emoji_levels[-1] if emoji_levels else '❓'
        
        can_level_up = current_level < max_level
        next_level = current_level + 1 if can_level_up else None
        next_emoji = emoji_levels[next_level] if next_level and next_level < len(emoji_levels) else None
        
        upgrade_cost = None
        can_upgrade = False
        if can_level_up and current_level < len(upgrade_energy):
            energy_cost = upgrade_energy[current_level]
            essence_cost = upgrade_essence[current_level] if current_level < len(upgrade_essence) else 0
            blocks_cost = upgrade_blocks[current_level] if current_level < len(upgrade_blocks) else 0
            
            upgrade_cost = {
                'energy': energy_cost,
                'essence': essence_cost,
                'blocks': blocks_cost
            }
            
            can_upgrade = (
                currencies['energy'] >= energy_cost and
                currencies['essence'] >= essence_cost and
                currencies['blocks'] >= blocks_cost
            )
        
        blueprint = ItemBlueprint(
            id=str(row[0]),
            code=row[1],
            name_en=row[2],
            name_zh=row[3],
            room=row[4],
            max_level=max_level,
            emoji_levels=emoji_levels,
            is_starter=row[7] or False,
            display_order=row[8] or 0
        )
        
        return UserItem(
            blueprint=blueprint,
            current_level=current_level,
            current_emoji=current_emoji,
            next_level=next_level,
            next_emoji=next_emoji,
            upgrade_cost=upgrade_cost,
            can_upgrade=can_upgrade,
            upgraded_at=row[13].isoformat() if row[13] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get item: {str(e)}")
    finally:
        db.close()

