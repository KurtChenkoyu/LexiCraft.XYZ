-- Migration: Three-Currency System for Building Economy
-- Created: December 8, 2025
-- Description: Adds Sparks, Essence, Energy, Blocks currencies and item building system

-- ============================================
-- STEP 1: Add Currency Columns to user_xp
-- ============================================

-- Add new currency columns to user_xp table
DO $$ 
BEGIN
    -- Sparks: Effort currency (earned from all activity)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_xp' AND column_name = 'sparks'
    ) THEN
        ALTER TABLE user_xp ADD COLUMN sparks INT DEFAULT 0 CHECK (sparks >= 0);
    END IF;

    -- Essence: Skill currency (earned from correct answers only)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_xp' AND column_name = 'essence'
    ) THEN
        ALTER TABLE user_xp ADD COLUMN essence INT DEFAULT 0 CHECK (essence >= 0);
    END IF;

    -- Energy: Building currency (earned from level-ups only)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_xp' AND column_name = 'energy'
    ) THEN
        ALTER TABLE user_xp ADD COLUMN energy INT DEFAULT 0 CHECK (energy >= 0);
    END IF;

    -- Solid Blocks: Mastered word count (building materials)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_xp' AND column_name = 'solid_blocks'
    ) THEN
        ALTER TABLE user_xp ADD COLUMN solid_blocks INT DEFAULT 0 CHECK (solid_blocks >= 0);
    END IF;
END $$;

-- ============================================
-- STEP 2: Item Blueprints Table
-- ============================================

CREATE TABLE IF NOT EXISTS item_blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    room VARCHAR(30) NOT NULL,  -- 'study', 'living'
    max_level INT DEFAULT 5 CHECK (max_level >= 1 AND max_level <= 10),
    emoji_levels TEXT[] NOT NULL,  -- Array of emoji per level: ['📦','🪑','📚','💼','🚀']
    is_starter BOOLEAN DEFAULT false,  -- Pre-installed for new users
    display_order INT DEFAULT 0,  -- Order within room
    
    -- Upgrade costs per level (arrays, index 0 = L1→L2, index 1 = L2→L3, etc.)
    upgrade_energy INT[] NOT NULL,   -- e.g., [5, 20, 40, 70]
    upgrade_essence INT[] NOT NULL,  -- e.g., [2, 10, 25, 45]
    upgrade_blocks INT[] NOT NULL,   -- e.g., [0, 1, 3, 6]
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blueprints_room ON item_blueprints(room);
CREATE INDEX IF NOT EXISTS idx_blueprints_starter ON item_blueprints(is_starter) WHERE is_starter = true;

-- ============================================
-- STEP 3: User Items Table
-- ============================================

CREATE TABLE IF NOT EXISTS user_items (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    blueprint_id UUID NOT NULL REFERENCES item_blueprints(id) ON DELETE CASCADE,
    current_level INT DEFAULT 0 CHECK (current_level >= 0),  -- 0 = broken/locked, 1+ = upgraded
    upgraded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, blueprint_id)
);

CREATE INDEX IF NOT EXISTS idx_user_items_user ON user_items(user_id);

-- ============================================
-- STEP 4: Currency Transaction History
-- ============================================

CREATE TABLE IF NOT EXISTS currency_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    currency_type VARCHAR(20) NOT NULL,  -- 'sparks', 'essence', 'energy', 'blocks'
    amount INT NOT NULL,  -- Positive for earned, negative for spent
    balance_after INT NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'mcq_correct', 'mcq_wrong', 'mcq_fast', 'review', 'level_up', 'word_mastered', 'item_upgrade'
    source_id UUID,  -- Reference to item, word, etc.
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_currency_tx_user ON currency_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_currency_tx_type ON currency_transactions(currency_type);
CREATE INDEX IF NOT EXISTS idx_currency_tx_date ON currency_transactions(created_at DESC);

-- ============================================
-- STEP 5: Helper Functions
-- ============================================

-- Function to get upgrade cost for an item at a given level
CREATE OR REPLACE FUNCTION get_upgrade_cost(
    p_blueprint_id UUID,
    p_current_level INT
)
RETURNS TABLE(
    energy_cost INT,
    essence_cost INT,
    blocks_cost INT
) AS $$
DECLARE
    v_energy_arr INT[];
    v_essence_arr INT[];
    v_blocks_arr INT[];
    v_max_level INT;
    v_idx INT;
BEGIN
    -- Get blueprint data
    SELECT upgrade_energy, upgrade_essence, upgrade_blocks, max_level
    INTO v_energy_arr, v_essence_arr, v_blocks_arr, v_max_level
    FROM item_blueprints
    WHERE id = p_blueprint_id;

    IF v_energy_arr IS NULL THEN
        RETURN;  -- Blueprint not found
    END IF;

    -- Check if already at max level
    IF p_current_level >= v_max_level THEN
        RETURN;  -- Already maxed
    END IF;

    -- Array index (PostgreSQL arrays are 1-based, level 0→1 uses index 1)
    v_idx := p_current_level + 1;

    -- Handle case where level exceeds array bounds
    IF v_idx > array_length(v_energy_arr, 1) THEN
        v_idx := array_length(v_energy_arr, 1);  -- Use last defined cost
    END IF;

    energy_cost := COALESCE(v_energy_arr[v_idx], 0);
    essence_cost := COALESCE(v_essence_arr[v_idx], 0);
    blocks_cost := COALESCE(v_blocks_arr[v_idx], 0);
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Function to initialize user items (called on first login)
CREATE OR REPLACE FUNCTION initialize_user_items(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Insert starter items at level 0 (broken state)
    INSERT INTO user_items (user_id, blueprint_id, current_level)
    SELECT p_user_id, id, 0
    FROM item_blueprints
    WHERE is_starter = true
    ON CONFLICT (user_id, blueprint_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Function to upgrade an item
CREATE OR REPLACE FUNCTION upgrade_item(
    p_user_id UUID,
    p_blueprint_code VARCHAR(50)
)
RETURNS TABLE(
    success BOOLEAN,
    error_code VARCHAR(50),
    new_level INT,
    energy_after INT,
    essence_after INT,
    blocks_after INT
) AS $$
DECLARE
    v_blueprint_id UUID;
    v_max_level INT;
    v_current_level INT;
    v_energy_cost INT;
    v_essence_cost INT;
    v_blocks_cost INT;
    v_user_energy INT;
    v_user_essence INT;
    v_user_blocks INT;
BEGIN
    -- Get blueprint
    SELECT id, max_level INTO v_blueprint_id, v_max_level
    FROM item_blueprints
    WHERE code = p_blueprint_code;

    IF v_blueprint_id IS NULL THEN
        success := false;
        error_code := 'BLUEPRINT_NOT_FOUND';
        RETURN NEXT;
        RETURN;
    END IF;

    -- Get or create user item
    SELECT current_level INTO v_current_level
    FROM user_items
    WHERE user_id = p_user_id AND blueprint_id = v_blueprint_id;

    IF v_current_level IS NULL THEN
        -- Create the item at level 0
        INSERT INTO user_items (user_id, blueprint_id, current_level)
        VALUES (p_user_id, v_blueprint_id, 0);
        v_current_level := 0;
    END IF;

    -- Check max level
    IF v_current_level >= v_max_level THEN
        success := false;
        error_code := 'ALREADY_MAX_LEVEL';
        RETURN NEXT;
        RETURN;
    END IF;

    -- Get upgrade cost
    SELECT gc.energy_cost, gc.essence_cost, gc.blocks_cost
    INTO v_energy_cost, v_essence_cost, v_blocks_cost
    FROM get_upgrade_cost(v_blueprint_id, v_current_level) gc;

    -- Get user currencies
    SELECT energy, essence, solid_blocks
    INTO v_user_energy, v_user_essence, v_user_blocks
    FROM user_xp
    WHERE user_id = p_user_id;

    -- Initialize if not exists
    IF v_user_energy IS NULL THEN
        INSERT INTO user_xp (user_id, energy, essence, solid_blocks, sparks, total_xp, current_level)
        VALUES (p_user_id, 0, 0, 0, 0, 0, 1)
        ON CONFLICT (user_id) DO NOTHING;
        
        v_user_energy := 0;
        v_user_essence := 0;
        v_user_blocks := 0;
    END IF;

    -- Check if user can afford
    IF v_user_energy < v_energy_cost THEN
        success := false;
        error_code := 'INSUFFICIENT_ENERGY';
        energy_after := v_user_energy;
        essence_after := v_user_essence;
        blocks_after := v_user_blocks;
        RETURN NEXT;
        RETURN;
    END IF;

    IF v_user_essence < v_essence_cost THEN
        success := false;
        error_code := 'INSUFFICIENT_ESSENCE';
        energy_after := v_user_energy;
        essence_after := v_user_essence;
        blocks_after := v_user_blocks;
        RETURN NEXT;
        RETURN;
    END IF;

    IF v_user_blocks < v_blocks_cost THEN
        success := false;
        error_code := 'INSUFFICIENT_BLOCKS';
        energy_after := v_user_energy;
        essence_after := v_user_essence;
        blocks_after := v_user_blocks;
        RETURN NEXT;
        RETURN;
    END IF;

    -- Deduct currencies
    UPDATE user_xp
    SET energy = energy - v_energy_cost,
        essence = essence - v_essence_cost,
        solid_blocks = solid_blocks - v_blocks_cost,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING energy, essence, solid_blocks
    INTO v_user_energy, v_user_essence, v_user_blocks;

    -- Record transactions
    IF v_energy_cost > 0 THEN
        INSERT INTO currency_transactions (user_id, currency_type, amount, balance_after, source, source_id, description)
        VALUES (p_user_id, 'energy', -v_energy_cost, v_user_energy, 'item_upgrade', v_blueprint_id, 'Upgrade ' || p_blueprint_code);
    END IF;

    IF v_essence_cost > 0 THEN
        INSERT INTO currency_transactions (user_id, currency_type, amount, balance_after, source, source_id, description)
        VALUES (p_user_id, 'essence', -v_essence_cost, v_user_essence, 'item_upgrade', v_blueprint_id, 'Upgrade ' || p_blueprint_code);
    END IF;

    IF v_blocks_cost > 0 THEN
        INSERT INTO currency_transactions (user_id, currency_type, amount, balance_after, source, source_id, description)
        VALUES (p_user_id, 'blocks', -v_blocks_cost, v_user_blocks, 'item_upgrade', v_blueprint_id, 'Upgrade ' || p_blueprint_code);
    END IF;

    -- Upgrade item
    UPDATE user_items
    SET current_level = current_level + 1,
        upgraded_at = NOW()
    WHERE user_id = p_user_id AND blueprint_id = v_blueprint_id
    RETURNING current_level INTO v_current_level;

    -- Return success
    success := true;
    error_code := NULL;
    new_level := v_current_level;
    energy_after := v_user_energy;
    essence_after := v_user_essence;
    blocks_after := v_user_blocks;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 6: Seed Item Blueprints
-- ============================================

INSERT INTO item_blueprints (code, name_en, name_zh, room, max_level, emoji_levels, is_starter, display_order, upgrade_energy, upgrade_essence, upgrade_blocks) VALUES
-- Study Room (書房)
('desk', 'Study Desk', '書桌', 'study', 5, 
    ARRAY['📦', '🪑', '📚', '💼', '🚀'],
    true, 1,
    ARRAY[0, 5, 20, 40, 70],      -- L0→1 free, then scaling
    ARRAY[0, 2, 10, 25, 45],
    ARRAY[0, 0, 1, 3, 6]),

('lamp', 'Desk Lamp', '檯燈', 'study', 4,
    ARRAY['💡', '🔦', '🪔', '✨'],
    true, 2,
    ARRAY[0, 3, 15, 35],
    ARRAY[0, 1, 8, 20],
    ARRAY[0, 0, 1, 2]),

('chair', 'Chair', '椅子', 'study', 3,
    ARRAY['🪑', '🛋️', '👑'],
    false, 3,
    ARRAY[3, 12, 30],
    ARRAY[1, 6, 15],
    ARRAY[0, 0, 2]),

('bookshelf', 'Bookshelf', '書架', 'study', 4,
    ARRAY['📖', '📚', '📕', '🏛️'],
    false, 4,
    ARRAY[6, 25, 50, 85],
    ARRAY[3, 12, 30, 55],
    ARRAY[0, 1, 4, 8]),

-- Living Room (客廳)
('plant', 'Plant', '植物', 'living', 4,
    ARRAY['🌱', '🌿', '🪴', '🌳'],
    false, 1,
    ARRAY[3, 12, 25, 45],
    ARRAY[1, 6, 15, 30],
    ARRAY[0, 0, 1, 3]),

('coffee_table', 'Coffee Table', '茶几', 'living', 3,
    ARRAY['🫖', '☕', '🍵'],
    false, 2,
    ARRAY[3, 12, 30],
    ARRAY[1, 6, 15],
    ARRAY[0, 0, 2]),

('tv', 'TV', '電視', 'living', 4,
    ARRAY['📺', '🖥️', '📽️', '🎬'],
    false, 3,
    ARRAY[6, 20, 45, 80],
    ARRAY[3, 10, 25, 50],
    ARRAY[0, 1, 3, 6]),

('sofa', 'Sofa', '沙發', 'living', 4,
    ARRAY['🛋️', '🛏️', '👑', '🏰'],
    false, 4,
    ARRAY[6, 25, 50, 90],
    ARRAY[3, 12, 30, 60],
    ARRAY[0, 1, 4, 8])

ON CONFLICT (code) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    room = EXCLUDED.room,
    max_level = EXCLUDED.max_level,
    emoji_levels = EXCLUDED.emoji_levels,
    is_starter = EXCLUDED.is_starter,
    display_order = EXCLUDED.display_order,
    upgrade_energy = EXCLUDED.upgrade_energy,
    upgrade_essence = EXCLUDED.upgrade_essence,
    upgrade_blocks = EXCLUDED.upgrade_blocks,
    updated_at = NOW();

-- ============================================
-- STEP 7: Comments
-- ============================================

COMMENT ON COLUMN user_xp.sparks IS 'Effort currency - earned from any activity';
COMMENT ON COLUMN user_xp.essence IS 'Skill currency - earned from correct answers only';
COMMENT ON COLUMN user_xp.energy IS 'Building currency - earned from level-ups only';
COMMENT ON COLUMN user_xp.solid_blocks IS 'Mastered words count - building materials';

COMMENT ON TABLE item_blueprints IS 'Definitions for buildable/upgradeable items in rooms';
COMMENT ON TABLE user_items IS 'User progress on each item';
COMMENT ON TABLE currency_transactions IS 'History of all currency changes';

COMMENT ON FUNCTION get_upgrade_cost IS 'Returns the cost to upgrade an item from its current level';
COMMENT ON FUNCTION initialize_user_items IS 'Creates starter items for new users';
COMMENT ON FUNCTION upgrade_item IS 'Attempts to upgrade an item, deducting currencies if successful';

