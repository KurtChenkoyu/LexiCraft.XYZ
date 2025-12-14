-- Migration: Seed MVP Achievements
-- Created: 2025-12
-- Description: Seeds the 20 MVP achievements into the achievements table

-- ============================================
-- ACHIEVEMENT TIERS & REWARDS
-- ============================================
-- Bronze (easy):    50 XP,  5 crystals
-- Silver (medium): 150 XP, 15 crystals
-- Gold (hard):     500 XP, 50 crystals
-- Platinum (epic): 1500 XP, 150 crystals

-- ============================================
-- ONBOARDING ACHIEVEMENTS (5)
-- ============================================

INSERT INTO achievements (code, name_en, name_zh, description_en, description_zh, icon, category, tier, requirement_type, requirement_value, xp_reward, crystal_reward) VALUES
('first_block', 'First Block', '第一塊', 'Forge your first vocabulary block', '鍛造你的第一個詞彙字塊', '🪨', 'onboarding', 'bronze', 'blocks_learned', 1, 50, 5),
('first_streak', 'Getting Started', '初露鋒芒', 'Achieve a 2-day learning streak', '達成2天連續學習', '🔥', 'onboarding', 'bronze', 'streak_days', 2, 50, 5),
('first_mastery', 'First Mastery', '初次掌握', 'Master your first block through verification', '通過驗證掌握第一個字塊', '✅', 'onboarding', 'bronze', 'blocks_mastered', 1, 50, 5),
('complete_survey', 'Self Discovery', '自我發現', 'Complete the vocabulary assessment survey', '完成詞彙評估調查', '📋', 'onboarding', 'bronze', 'survey_complete', 1, 50, 5),
('first_challenge', 'Challenge Accepted', '接受挑戰', 'Complete your first Challenge Mode session', '完成第一次挑戰模式', '⚡', 'onboarding', 'silver', 'challenges_completed', 1, 150, 15)
ON CONFLICT (code) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    description_en = EXCLUDED.description_en,
    description_zh = EXCLUDED.description_zh,
    icon = EXCLUDED.icon,
    category = EXCLUDED.category,
    tier = EXCLUDED.tier,
    requirement_type = EXCLUDED.requirement_type,
    requirement_value = EXCLUDED.requirement_value,
    xp_reward = EXCLUDED.xp_reward,
    crystal_reward = EXCLUDED.crystal_reward;

-- ============================================
-- STREAK ACHIEVEMENTS (6)
-- ============================================

INSERT INTO achievements (code, name_en, name_zh, description_en, description_zh, icon, category, tier, requirement_type, requirement_value, xp_reward, crystal_reward) VALUES
('streak_3', 'Three''s Company', '連三之力', 'Maintain a 3-day learning streak', '維持3天連續學習', '🔥', 'streak', 'bronze', 'streak_days', 3, 50, 5),
('streak_7', 'Week Warrior', '週戰士', 'Maintain a 7-day learning streak', '維持7天連續學習', '🗡️', 'streak', 'silver', 'streak_days', 7, 150, 15),
('streak_14', 'Fortnight Fighter', '雙週鬥士', 'Maintain a 14-day learning streak', '維持14天連續學習', '⚔️', 'streak', 'silver', 'streak_days', 14, 150, 15),
('streak_30', 'Month Master', '月之大師', 'Maintain a 30-day learning streak', '維持30天連續學習', '🏆', 'streak', 'gold', 'streak_days', 30, 500, 50),
('streak_60', 'Dedicated Miner', '專注礦工', 'Maintain a 60-day learning streak', '維持60天連續學習', '💪', 'streak', 'gold', 'streak_days', 60, 500, 50),
('streak_100', 'Century Miner', '百日礦工', 'Maintain a 100-day learning streak', '維持100天連續學習', '💯', 'streak', 'platinum', 'streak_days', 100, 1500, 150)
ON CONFLICT (code) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    description_en = EXCLUDED.description_en,
    description_zh = EXCLUDED.description_zh,
    icon = EXCLUDED.icon,
    category = EXCLUDED.category,
    tier = EXCLUDED.tier,
    requirement_type = EXCLUDED.requirement_type,
    requirement_value = EXCLUDED.requirement_value,
    xp_reward = EXCLUDED.xp_reward,
    crystal_reward = EXCLUDED.crystal_reward;

-- ============================================
-- VOLUME/VOCABULARY ACHIEVEMENTS (8)
-- ============================================

INSERT INTO achievements (code, name_en, name_zh, description_en, description_zh, icon, category, tier, requirement_type, requirement_value, xp_reward, crystal_reward) VALUES
('vocab_10', 'First Ten', '初試十塊', 'Learn 10 vocabulary blocks', '學習10個詞彙字塊', '📚', 'vocabulary', 'bronze', 'blocks_learned', 10, 50, 5),
('vocab_25', 'Quarter Century', '二十五塊', 'Learn 25 vocabulary blocks', '學習25個詞彙字塊', '📖', 'vocabulary', 'bronze', 'blocks_learned', 25, 50, 5),
('vocab_50', 'Half Century', '半百之塊', 'Learn 50 vocabulary blocks', '學習50個詞彙字塊', '📕', 'vocabulary', 'silver', 'blocks_learned', 50, 150, 15),
('vocab_100', 'Century', '百塊達成', 'Learn 100 vocabulary blocks', '學習100個詞彙字塊', '📗', 'vocabulary', 'silver', 'blocks_learned', 100, 150, 15),
('vocab_250', 'Word Collector', '詞彙收集家', 'Learn 250 vocabulary blocks', '學習250個詞彙字塊', '📘', 'vocabulary', 'gold', 'blocks_learned', 250, 500, 50),
('vocab_500', 'Vocabulary Expert', '詞彙專家', 'Learn 500 vocabulary blocks', '學習500個詞彙字塊', '📙', 'vocabulary', 'gold', 'blocks_learned', 500, 500, 50),
('vocab_1000', 'Vocabulary Master', '詞彙大師', 'Learn 1000 vocabulary blocks', '學習1000個詞彙字塊', '🎓', 'vocabulary', 'platinum', 'blocks_learned', 1000, 1500, 150),
('vocab_2000', 'Lexicon Legend', '詞海傳奇', 'Learn 2000 vocabulary blocks', '學習2000個詞彙字塊', '👑', 'vocabulary', 'platinum', 'blocks_learned', 2000, 1500, 150)
ON CONFLICT (code) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    description_en = EXCLUDED.description_en,
    description_zh = EXCLUDED.description_zh,
    icon = EXCLUDED.icon,
    category = EXCLUDED.category,
    tier = EXCLUDED.tier,
    requirement_type = EXCLUDED.requirement_type,
    requirement_value = EXCLUDED.requirement_value,
    xp_reward = EXCLUDED.xp_reward,
    crystal_reward = EXCLUDED.crystal_reward;

-- ============================================
-- MASTERY ACHIEVEMENTS (6)
-- ============================================

INSERT INTO achievements (code, name_en, name_zh, description_en, description_zh, icon, category, tier, requirement_type, requirement_value, xp_reward, crystal_reward) VALUES
('master_1', 'Verified', '已驗證', 'Master 1 vocabulary block', '掌握1個詞彙字塊', '✓', 'mastery', 'bronze', 'blocks_mastered', 1, 50, 5),
('master_10', 'Proven Knowledge', '實力證明', 'Master 10 vocabulary blocks', '掌握10個詞彙字塊', '✅', 'mastery', 'silver', 'blocks_mastered', 10, 150, 15),
('master_25', 'Knowledge Builder', '知識建造者', 'Master 25 vocabulary blocks', '掌握25個詞彙字塊', '🔨', 'mastery', 'silver', 'blocks_mastered', 25, 150, 15),
('master_50', 'Solid Foundation', '穩固基礎', 'Master 50 vocabulary blocks', '掌握50個詞彙字塊', '🧱', 'mastery', 'gold', 'blocks_mastered', 50, 500, 50),
('master_100', 'Century Master', '百塊精通', 'Master 100 vocabulary blocks', '掌握100個詞彙字塊', '🏛️', 'mastery', 'gold', 'blocks_mastered', 100, 500, 50),
('master_500', 'Grand Master', '大師級', 'Master 500 vocabulary blocks', '掌握500個詞彙字塊', '🏆', 'mastery', 'platinum', 'blocks_mastered', 500, 1500, 150)
ON CONFLICT (code) DO UPDATE SET
    name_en = EXCLUDED.name_en,
    name_zh = EXCLUDED.name_zh,
    description_en = EXCLUDED.description_en,
    description_zh = EXCLUDED.description_zh,
    icon = EXCLUDED.icon,
    category = EXCLUDED.category,
    tier = EXCLUDED.tier,
    requirement_type = EXCLUDED.requirement_type,
    requirement_value = EXCLUDED.requirement_value,
    xp_reward = EXCLUDED.xp_reward,
    crystal_reward = EXCLUDED.crystal_reward;

-- ============================================
-- Verify achievement count
-- ============================================

DO $$
DECLARE
    achievement_count INT;
BEGIN
    SELECT COUNT(*) INTO achievement_count FROM achievements;
    RAISE NOTICE 'Total achievements seeded: %', achievement_count;
END $$;

