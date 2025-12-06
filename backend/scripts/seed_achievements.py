"""
Seed Achievement Definitions

Populates the achievements table with predefined achievements.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Achievement definitions
ACHIEVEMENTS = [
    # Streak Achievements
    {
        'code': 'streak_3',
        'name_en': 'Getting Started',
        'name_zh': '開始學習',
        'description_en': 'Maintain a 3-day learning streak',
        'description_zh': '連續學習3天',
        'icon': '🔥',
        'category': 'streak',
        'tier': 'bronze',
        'requirement_type': 'streak_days',
        'requirement_value': 3,
        'xp_reward': 25,
        'points_bonus': 0
    },
    {
        'code': 'streak_7',
        'name_en': 'Week Warrior',
        'name_zh': '一週戰士',
        'description_en': 'Maintain a 7-day learning streak',
        'description_zh': '連續學習7天',
        'icon': '🔥',
        'category': 'streak',
        'tier': 'silver',
        'requirement_type': 'streak_days',
        'requirement_value': 7,
        'xp_reward': 50,
        'points_bonus': 10
    },
    {
        'code': 'streak_30',
        'name_en': 'Monthly Master',
        'name_zh': '月度大師',
        'description_en': 'Maintain a 30-day learning streak',
        'description_zh': '連續學習30天',
        'icon': '🔥',
        'category': 'streak',
        'tier': 'gold',
        'requirement_type': 'streak_days',
        'requirement_value': 30,
        'xp_reward': 150,
        'points_bonus': 50
    },
    {
        'code': 'streak_100',
        'name_en': 'Centurion',
        'name_zh': '百天勇士',
        'description_en': 'Maintain a 100-day learning streak',
        'description_zh': '連續學習100天',
        'icon': '🔥',
        'category': 'streak',
        'tier': 'platinum',
        'requirement_type': 'streak_days',
        'requirement_value': 100,
        'xp_reward': 500,
        'points_bonus': 200
    },
    
    # Vocabulary Milestones
    {
        'code': 'vocab_100',
        'name_en': 'Century Club',
        'name_zh': '百字俱樂部',
        'description_en': 'Learn 100 words',
        'description_zh': '學會100個單字',
        'icon': '📚',
        'category': 'vocabulary',
        'tier': 'bronze',
        'requirement_type': 'vocabulary_size',
        'requirement_value': 100,
        'xp_reward': 50,
        'points_bonus': 20
    },
    {
        'code': 'vocab_500',
        'name_en': 'Half Thousand',
        'name_zh': '五百字達人',
        'description_en': 'Learn 500 words',
        'description_zh': '學會500個單字',
        'icon': '📚',
        'category': 'vocabulary',
        'tier': 'silver',
        'requirement_type': 'vocabulary_size',
        'requirement_value': 500,
        'xp_reward': 150,
        'points_bonus': 75
    },
    {
        'code': 'vocab_1000',
        'name_en': 'Thousand Words',
        'name_zh': '千字大師',
        'description_en': 'Learn 1,000 words',
        'description_zh': '學會1,000個單字',
        'icon': '📚',
        'category': 'vocabulary',
        'tier': 'gold',
        'requirement_type': 'vocabulary_size',
        'requirement_value': 1000,
        'xp_reward': 300,
        'points_bonus': 150
    },
    {
        'code': 'vocab_2500',
        'name_en': 'Vocabulary Expert',
        'name_zh': '詞彙專家',
        'description_en': 'Learn 2,500 words',
        'description_zh': '學會2,500個單字',
        'icon': '📚',
        'category': 'vocabulary',
        'tier': 'platinum',
        'requirement_type': 'vocabulary_size',
        'requirement_value': 2500,
        'xp_reward': 500,
        'points_bonus': 300
    },
    
    # Mastery Achievements
    {
        'code': 'master_first',
        'name_en': 'First Mastery',
        'name_zh': '首次精通',
        'description_en': 'Master your first word',
        'description_zh': '精通第一個單字',
        'icon': '⭐',
        'category': 'mastery',
        'tier': 'bronze',
        'requirement_type': 'mastered_count',
        'requirement_value': 1,
        'xp_reward': 25,
        'points_bonus': 0
    },
    {
        'code': 'master_10',
        'name_en': 'Decade Master',
        'name_zh': '十全十美',
        'description_en': 'Master 10 words',
        'description_zh': '精通10個單字',
        'icon': '⭐',
        'category': 'mastery',
        'tier': 'silver',
        'requirement_type': 'mastered_count',
        'requirement_value': 10,
        'xp_reward': 75,
        'points_bonus': 30
    },
    {
        'code': 'master_50',
        'name_en': 'Half Century',
        'name_zh': '五十精通',
        'description_en': 'Master 50 words',
        'description_zh': '精通50個單字',
        'icon': '⭐',
        'category': 'mastery',
        'tier': 'gold',
        'requirement_type': 'mastered_count',
        'requirement_value': 50,
        'xp_reward': 200,
        'points_bonus': 100
    },
    {
        'code': 'master_100',
        'name_en': 'Century Master',
        'name_zh': '百字精通',
        'description_en': 'Master 100 words',
        'description_zh': '精通100個單字',
        'icon': '⭐',
        'category': 'mastery',
        'tier': 'platinum',
        'requirement_type': 'mastered_count',
        'requirement_value': 100,
        'xp_reward': 400,
        'points_bonus': 200
    },
    
    # Weekly Achievements
    {
        'code': 'week_10',
        'name_en': 'Weekly Learner',
        'name_zh': '每週學習者',
        'description_en': 'Learn 10 words this week',
        'description_zh': '本週學會10個單字',
        'icon': '📅',
        'category': 'special',
        'tier': 'bronze',
        'requirement_type': 'words_this_week',
        'requirement_value': 10,
        'xp_reward': 30,
        'points_bonus': 10
    },
    {
        'code': 'week_25',
        'name_en': 'Weekly Champion',
        'name_zh': '每週冠軍',
        'description_en': 'Learn 25 words this week',
        'description_zh': '本週學會25個單字',
        'icon': '📅',
        'category': 'special',
        'tier': 'silver',
        'requirement_type': 'words_this_week',
        'requirement_value': 25,
        'xp_reward': 75,
        'points_bonus': 30
    },
    {
        'code': 'perfect_week',
        'name_en': 'Perfect Week',
        'name_zh': '完美一週',
        'description_en': 'Learn every day for a week',
        'description_zh': '一週內每天學習',
        'icon': '✨',
        'category': 'special',
        'tier': 'gold',
        'requirement_type': 'perfect_week',
        'requirement_value': 7,
        'xp_reward': 100,
        'points_bonus': 50
    },
    
    # Review Achievements
    {
        'code': 'reviews_100',
        'name_en': 'Reviewer',
        'name_zh': '複習者',
        'description_en': 'Complete 100 reviews',
        'description_zh': '完成100次複習',
        'icon': '🔄',
        'category': 'special',
        'tier': 'bronze',
        'requirement_type': 'total_reviews',
        'requirement_value': 100,
        'xp_reward': 50,
        'points_bonus': 20
    },
    {
        'code': 'reviews_500',
        'name_en': 'Dedicated Reviewer',
        'name_zh': '專注複習者',
        'description_en': 'Complete 500 reviews',
        'description_zh': '完成500次複習',
        'icon': '🔄',
        'category': 'special',
        'tier': 'silver',
        'requirement_type': 'total_reviews',
        'requirement_value': 500,
        'xp_reward': 150,
        'points_bonus': 75
    }
]


def seed_achievements():
    """Seed achievements into the database."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        for achievement in ACHIEVEMENTS:
            # Check if achievement already exists
            result = session.execute(
                text("SELECT id FROM achievements WHERE code = :code"),
                {'code': achievement['code']}
            )
            existing = result.fetchone()
            
            if existing:
                print(f"Achievement {achievement['code']} already exists, skipping...")
                continue
            
            # Insert achievement
            session.execute(
                text("""
                    INSERT INTO achievements (
                        code, name_en, name_zh, description_en, description_zh,
                        icon, category, tier, requirement_type, requirement_value,
                        xp_reward, points_bonus
                    ) VALUES (
                        :code, :name_en, :name_zh, :description_en, :description_zh,
                        :icon, :category, :tier, :requirement_type, :requirement_value,
                        :xp_reward, :points_bonus
                    )
                """),
                achievement
            )
            print(f"Seeded achievement: {achievement['code']} - {achievement['name_en']}")
        
        session.commit()
        print(f"\nSuccessfully seeded {len(ACHIEVEMENTS)} achievements!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding achievements: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_achievements()


