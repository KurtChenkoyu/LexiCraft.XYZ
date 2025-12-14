-- Migration: Level & Achievement System Enhancement
-- Created: 2025-12
-- Description: Adds level unlocks, crystal economy, prestige system, and cosmetics

-- ============================================
-- STEP 1: Level Unlocks System
-- ============================================

-- Level unlock definitions (what unlocks at each level)
CREATE TABLE IF NOT EXISTS level_unlocks (
    id SERIAL PRIMARY KEY,
    level INT NOT NULL,
    unlock_type VARCHAR(30) NOT NULL,  -- 'content', 'feature', 'social', 'cosmetic', 'status'
    unlock_code VARCHAR(50) NOT NULL,  -- 'tier_3_blocks', 'friend_list', 'challenge_mode', etc.
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    description_en TEXT,
    description_zh TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_level_unlocks_level ON level_unlocks(level);
CREATE INDEX IF NOT EXISTS idx_level_unlocks_type ON level_unlocks(unlock_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_level_unlocks_code ON level_unlocks(unlock_code);

-- ============================================
-- STEP 2: Crystal Economy
-- ============================================

-- User crystal balance
CREATE TABLE IF NOT EXISTS user_crystals (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    balance INT DEFAULT 0 CHECK (balance >= 0),
    lifetime_earned INT DEFAULT 0,
    lifetime_spent INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Crystal transaction history
CREATE TABLE IF NOT EXISTS crystal_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount INT NOT NULL,  -- Positive for earned, negative for spent
    balance_after INT NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'achievement', 'streak_milestone', 'prestige', 'purchase'
    source_id UUID,  -- Reference to achievement_id, etc.
    description_en VARCHAR(200),
    description_zh VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crystal_transactions_user ON crystal_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_crystal_transactions_date ON crystal_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crystal_transactions_source ON crystal_transactions(source);

-- ============================================
-- STEP 3: Prestige System
-- ============================================

-- User prestige tracking
CREATE TABLE IF NOT EXISTS user_prestige (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    prestige_level INT DEFAULT 0 CHECK (prestige_level >= 0 AND prestige_level <= 10),
    total_xp_earned_lifetime BIGINT DEFAULT 0,
    last_prestige_at TIMESTAMPTZ,
    xp_bonus_multiplier DECIMAL(3,2) DEFAULT 1.00,  -- 1.05 per prestige level
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- STEP 4: Cosmetics System
-- ============================================

-- Cosmetic item definitions
CREATE TABLE IF NOT EXISTS cosmetics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(30) NOT NULL,  -- 'pickaxe', 'frame', 'title', 'theme', 'badge'
    name_en VARCHAR(100) NOT NULL,
    name_zh VARCHAR(100),
    description_en TEXT,
    description_zh TEXT,
    icon VARCHAR(100),  -- Icon URL or emoji
    rarity VARCHAR(20) DEFAULT 'common',  -- 'common', 'uncommon', 'rare', 'epic', 'legendary'
    unlock_type VARCHAR(30) NOT NULL,  -- 'level', 'achievement', 'prestige', 'crystal_purchase', 'special'
    unlock_requirement VARCHAR(100),  -- 'level_10', 'achievement_streak_30', 'prestige_1', etc.
    crystal_cost INT,  -- If purchasable with crystals
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cosmetics_type ON cosmetics(type);
CREATE INDEX IF NOT EXISTS idx_cosmetics_unlock_type ON cosmetics(unlock_type);
CREATE INDEX IF NOT EXISTS idx_cosmetics_rarity ON cosmetics(rarity);

-- User cosmetic ownership and equipment
CREATE TABLE IF NOT EXISTS user_cosmetics (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    cosmetic_id UUID NOT NULL REFERENCES cosmetics(id) ON DELETE CASCADE,
    equipped BOOLEAN DEFAULT false,
    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, cosmetic_id)
);

CREATE INDEX IF NOT EXISTS idx_user_cosmetics_user ON user_cosmetics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_cosmetics_equipped ON user_cosmetics(user_id, equipped) WHERE equipped = true;

-- ============================================
-- STEP 5: Add crystal_reward to achievements table
-- ============================================

-- Add crystal_reward column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'achievements' AND column_name = 'crystal_reward'
    ) THEN
        ALTER TABLE achievements ADD COLUMN crystal_reward INT DEFAULT 0;
    END IF;
END $$;

-- ============================================
-- STEP 6: Helper Functions
-- ============================================

-- Function to initialize user crystals
CREATE OR REPLACE FUNCTION initialize_user_crystals(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_crystals (user_id, balance, lifetime_earned, lifetime_spent)
    VALUES (p_user_id, 0, 0, 0)
    ON CONFLICT (user_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Function to add crystals to user
CREATE OR REPLACE FUNCTION add_crystals(
    p_user_id UUID,
    p_amount INT,
    p_source VARCHAR(50),
    p_source_id UUID DEFAULT NULL,
    p_description_en VARCHAR(200) DEFAULT NULL,
    p_description_zh VARCHAR(200) DEFAULT NULL
)
RETURNS INT AS $$
DECLARE
    v_new_balance INT;
BEGIN
    -- Initialize if not exists
    PERFORM initialize_user_crystals(p_user_id);
    
    -- Update balance
    UPDATE user_crystals
    SET balance = balance + p_amount,
        lifetime_earned = lifetime_earned + p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING balance INTO v_new_balance;
    
    -- Record transaction
    INSERT INTO crystal_transactions (
        user_id, amount, balance_after, source, source_id, description_en, description_zh
    )
    VALUES (
        p_user_id, p_amount, v_new_balance, p_source, p_source_id, p_description_en, p_description_zh
    );
    
    RETURN v_new_balance;
END;
$$ LANGUAGE plpgsql;

-- Function to spend crystals
CREATE OR REPLACE FUNCTION spend_crystals(
    p_user_id UUID,
    p_amount INT,
    p_source VARCHAR(50),
    p_source_id UUID DEFAULT NULL,
    p_description_en VARCHAR(200) DEFAULT NULL,
    p_description_zh VARCHAR(200) DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_balance INT;
    v_new_balance INT;
BEGIN
    -- Get current balance
    SELECT balance INTO v_current_balance
    FROM user_crystals
    WHERE user_id = p_user_id;
    
    -- Check sufficient balance
    IF v_current_balance IS NULL OR v_current_balance < p_amount THEN
        RETURN FALSE;
    END IF;
    
    -- Update balance
    UPDATE user_crystals
    SET balance = balance - p_amount,
        lifetime_spent = lifetime_spent + p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING balance INTO v_new_balance;
    
    -- Record transaction (negative amount for spending)
    INSERT INTO crystal_transactions (
        user_id, amount, balance_after, source, source_id, description_en, description_zh
    )
    VALUES (
        p_user_id, -p_amount, v_new_balance, p_source, p_source_id, p_description_en, p_description_zh
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to initialize user prestige
CREATE OR REPLACE FUNCTION initialize_user_prestige(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_prestige (user_id, prestige_level, xp_bonus_multiplier)
    VALUES (p_user_id, 0, 1.00)
    ON CONFLICT (user_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's unlocked features by level
CREATE OR REPLACE FUNCTION get_unlocked_features(p_user_level INT)
RETURNS TABLE(
    unlock_code VARCHAR(50),
    unlock_type VARCHAR(30),
    name_en VARCHAR(100),
    name_zh VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT lu.unlock_code, lu.unlock_type, lu.name_en, lu.name_zh
    FROM level_unlocks lu
    WHERE lu.level <= p_user_level
    ORDER BY lu.level;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has unlocked a specific feature
CREATE OR REPLACE FUNCTION has_unlock(p_user_id UUID, p_unlock_code VARCHAR(50))
RETURNS BOOLEAN AS $$
DECLARE
    v_user_level INT;
    v_required_level INT;
BEGIN
    -- Get user's current level
    SELECT current_level INTO v_user_level
    FROM user_xp
    WHERE user_id = p_user_id;
    
    IF v_user_level IS NULL THEN
        v_user_level := 1;
    END IF;
    
    -- Get required level for this unlock
    SELECT level INTO v_required_level
    FROM level_unlocks
    WHERE unlock_code = p_unlock_code;
    
    IF v_required_level IS NULL THEN
        RETURN FALSE;  -- Unknown unlock code
    END IF;
    
    RETURN v_user_level >= v_required_level;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 7: Seed Level Unlocks
-- ============================================

INSERT INTO level_unlocks (level, unlock_type, unlock_code, name_en, name_zh, description_en, description_zh, icon) VALUES
-- Tier 1: Foundation (1-20)
(1, 'content', 'tier_1_blocks', 'Basic Blocks', '基礎字塊', 'Access to Tier 1 basic vocabulary blocks', '可以訪問第一階基礎詞彙字塊', '🪨'),
(1, 'content', 'tier_2_blocks', 'Multi-meaning Blocks', '多義字塊', 'Access to Tier 2 multi-meaning blocks', '可以訪問第二階多義詞字塊', '🧱'),
(3, 'feature', 'profile_badges', 'Profile Badges', '個人徽章', 'Display achievement badges on your profile', '可以在個人頁面顯示成就徽章', '🏅'),
(5, 'content', 'tier_3_blocks', 'Phrase Blocks', '片語字塊', 'Access to Tier 3 phrase blocks', '可以訪問第三階片語字塊', '📝'),
(5, 'feature', 'streak_freeze', 'Streak Freeze', '連續保護', 'Purchase streak freeze with crystals', '可以用水晶購買連續保護', '🧊'),
(10, 'content', 'tier_4_blocks', 'Idiom Blocks', '成語字塊', 'Access to Tier 4 idiom blocks', '可以訪問第四階成語字塊', '📚'),
(10, 'feature', 'challenge_mode', 'Challenge Mode', '挑戰模式', 'Timed MCQs for bonus XP', '限時答題獲得額外經驗值', '⚡'),
(15, 'content', 'tier_5_blocks', 'Pattern Blocks', '詞綴字塊', 'Access to Tier 5 morphological patterns', '可以訪問第五階詞綴字塊', '🔗'),
(15, 'content', 'tier_6_blocks', 'Register Blocks', '語域字塊', 'Access to Tier 6 formal/informal variants', '可以訪問第六階正式/非正式變體', '📋'),
(15, 'content', 'tier_7_blocks', 'Context Blocks', '語境字塊', 'Access to Tier 7 context-specific meanings', '可以訪問第七階語境特定含義', '🎯'),
(20, 'social', 'friend_list', 'Friend List', '好友名單', 'Add friends and view their progress', '可以添加好友並查看他們的進度', '👥'),

-- Tier 2: Social (20-40)
(25, 'social', 'leaderboards', 'Leaderboards', '排行榜', 'Weekly and monthly leaderboards', '每週和每月排行榜', '🏆'),
(30, 'social', 'mining_guilds', 'Mining Guilds', '礦工公會', 'Create or join study groups', '創建或加入學習小組', '⛏️'),
(35, 'social', 'peer_coaching', 'Peer Coaching', '同儕指導', 'Help others learn for bonus XP', '幫助他人學習獲得額外經驗值', '🎓'),
(40, 'social', 'guild_challenges', 'Guild Challenges', '公會挑戰', 'Compete in guild challenges', '參與公會挑戰賽', '🏁'),

-- Tier 3: Mastery (40-60)
(40, 'feature', 'expert_mode', 'Expert Mode', '專家模式', 'Harder MCQs with 1.5x XP multiplier', '更難的題目，1.5倍經驗值', '🎯'),
(45, 'feature', 'mining_expeditions', 'Mining Expeditions', '探礦遠征', 'Themed vocabulary challenges', '主題詞彙挑戰', '🗺️'),
(50, 'status', 'master_miner', 'Master Miner Title', '大師礦工頭銜', 'Prestigious title and mentor access', '尊貴頭銜和導師權限', '👑'),
(55, 'cosmetic', 'profile_themes', 'Profile Themes', '個人主題', 'Customize your profile appearance', '自定義個人頁面外觀', '🎨'),
(60, 'status', 'legend_status', 'Legend Status', '傳奇地位', 'Elite status with beta feature access', '精英地位，可優先體驗新功能', '⭐')

ON CONFLICT (unlock_code) DO UPDATE SET
    level = EXCLUDED.level,
    unlock_type = EXCLUDED.unlock_type,
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    description_en = EXCLUDED.description_en,
    description_zh = EXCLUDED.description_zh,
    icon = EXCLUDED.icon;

-- ============================================
-- STEP 8: Seed Initial Cosmetics
-- ============================================

INSERT INTO cosmetics (code, type, name_en, name_zh, description_en, description_zh, icon, rarity, unlock_type, unlock_requirement, crystal_cost) VALUES
-- Level-based pickaxes
('pickaxe_basic', 'pickaxe', 'Basic Pickaxe', '基礎鎬', 'A simple mining pickaxe', '一把簡單的挖礦鎬', '⛏️', 'common', 'level', 'level_1', NULL),
('pickaxe_iron', 'pickaxe', 'Iron Pickaxe', '鐵鎬', 'A sturdy iron pickaxe', '一把堅固的鐵鎬', '🔨', 'uncommon', 'level', 'level_10', NULL),
('pickaxe_gold', 'pickaxe', 'Golden Pickaxe', '金鎬', 'A gleaming golden pickaxe', '一把閃閃發光的金鎬', '✨', 'rare', 'level', 'level_25', NULL),
('pickaxe_diamond', 'pickaxe', 'Diamond Pickaxe', '鑽石鎬', 'A legendary diamond pickaxe', '一把傳說中的鑽石鎬', '💎', 'epic', 'level', 'level_40', NULL),
('pickaxe_master', 'pickaxe', 'Master Pickaxe', '大師鎬', 'The ultimate mining tool', '終極挖礦工具', '🌟', 'legendary', 'level', 'level_60', NULL),

-- Avatar frames
('frame_basic', 'frame', 'Basic Frame', '基礎邊框', 'A simple profile frame', '簡單的個人邊框', '⬜', 'common', 'level', 'level_1', NULL),
('frame_bronze', 'frame', 'Bronze Frame', '銅邊框', 'A bronze profile frame', '銅色個人邊框', '🟫', 'uncommon', 'level', 'level_15', NULL),
('frame_silver', 'frame', 'Silver Frame', '銀邊框', 'A silver profile frame', '銀色個人邊框', '⬛', 'rare', 'level', 'level_30', NULL),
('frame_gold', 'frame', 'Gold Frame', '金邊框', 'A gold profile frame', '金色個人邊框', '🟨', 'epic', 'level', 'level_45', NULL),
('frame_diamond', 'frame', 'Diamond Frame', '鑽石邊框', 'A diamond profile frame', '鑽石個人邊框', '💠', 'legendary', 'level', 'level_60', NULL),

-- Achievement-based titles
('title_beginner', 'title', 'Beginner Miner', '初學礦工', 'For taking the first steps', '邁出第一步', '🌱', 'common', 'achievement', 'first_block', NULL),
('title_week_warrior', 'title', 'Week Warrior', '週戰士', 'For maintaining a 7-day streak', '維持7天連續學習', '🗡️', 'uncommon', 'achievement', 'streak_7', NULL),
('title_century_miner', 'title', 'Century Miner', '百日礦工', 'For maintaining a 100-day streak', '維持100天連續學習', '💯', 'legendary', 'achievement', 'streak_100', NULL),
('title_vocabulary_master', 'title', 'Vocabulary Master', '詞彙大師', 'For learning 1000 words', '學習1000個單詞', '📖', 'epic', 'achievement', 'vocab_1000', NULL),

-- Crystal purchasable cosmetics
('pickaxe_neon', 'pickaxe', 'Neon Pickaxe', '霓虹鎬', 'A glowing neon pickaxe', '發光的霓虹鎬', '🔮', 'rare', 'crystal_purchase', NULL, 100),
('frame_rainbow', 'frame', 'Rainbow Frame', '彩虹邊框', 'A colorful rainbow frame', '彩色彩虹邊框', '🌈', 'rare', 'crystal_purchase', NULL, 150),
('title_collector', 'title', 'Collector', '收藏家', 'For the dedicated collector', '獻給專注的收藏家', '🎭', 'uncommon', 'crystal_purchase', NULL, 50),

-- Prestige cosmetics
('frame_prestige_1', 'frame', 'Prestige Frame I', '榮耀邊框 I', 'First prestige frame', '第一次榮耀邊框', '⭐', 'epic', 'prestige', 'prestige_1', NULL),
('frame_prestige_5', 'frame', 'Prestige Frame V', '榮耀邊框 V', 'Fifth prestige frame', '第五次榮耀邊框', '🌟', 'legendary', 'prestige', 'prestige_5', NULL),
('title_prestige_master', 'title', 'Prestige Master', '榮耀大師', 'For reaching prestige 10', '達到榮耀10級', '👑', 'legendary', 'prestige', 'prestige_10', NULL)

ON CONFLICT (code) DO UPDATE SET
    type = EXCLUDED.type,
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    description_en = EXCLUDED.description_en,
    description_zh = EXCLUDED.description_zh,
    icon = EXCLUDED.icon,
    rarity = EXCLUDED.rarity,
    unlock_type = EXCLUDED.unlock_type,
    unlock_requirement = EXCLUDED.unlock_requirement,
    crystal_cost = EXCLUDED.crystal_cost;

-- ============================================
-- STEP 9: Comments
-- ============================================

COMMENT ON TABLE level_unlocks IS 'Defines what content/features unlock at each level';
COMMENT ON TABLE user_crystals IS 'User crystal balance for premium-lite currency';
COMMENT ON TABLE crystal_transactions IS 'History of crystal earnings and spending';
COMMENT ON TABLE user_prestige IS 'User prestige level and bonuses';
COMMENT ON TABLE cosmetics IS 'Cosmetic item definitions (pickaxes, frames, titles, themes)';
COMMENT ON TABLE user_cosmetics IS 'User cosmetic ownership and equipped status';

COMMENT ON FUNCTION initialize_user_crystals IS 'Initializes crystal balance for a new user';
COMMENT ON FUNCTION add_crystals IS 'Adds crystals to user balance and records transaction';
COMMENT ON FUNCTION spend_crystals IS 'Spends crystals from user balance, returns false if insufficient';
COMMENT ON FUNCTION initialize_user_prestige IS 'Initializes prestige record for a new user';
COMMENT ON FUNCTION get_unlocked_features IS 'Returns all features unlocked at or below given level';
COMMENT ON FUNCTION has_unlock IS 'Checks if user has unlocked a specific feature by level';

