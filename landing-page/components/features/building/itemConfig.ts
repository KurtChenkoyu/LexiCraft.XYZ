/**
 * Item Configuration - Bonuses, Descriptions, and Level Details
 * 
 * Each item has bonuses that stack per level. Users can see these on hover.
 */

export type BonusType = 'sparks' | 'energy' | 'essence' | 'blocks'

export interface ItemBonus {
  type: BonusType
  value: number // Percentage bonus (e.g., 0.01 = +0.01%)
}

export interface LevelDetail {
  name_en: string
  name_zh: string
  description_en: string
  description_zh: string
  bonus: ItemBonus | null
}

export interface ItemFullConfig {
  code: string
  name_en: string
  name_zh: string
  description_en: string
  description_zh: string
  levels: LevelDetail[]
}

export const ITEM_CONFIGS: Record<string, ItemFullConfig> = {
  desk: {
    code: 'desk',
    name_en: 'Study Desk',
    name_zh: '書桌',
    description_en: 'Where all great learning begins. A proper desk helps you focus and absorb knowledge.',
    description_zh: '所有偉大學習的起點。一張合適的書桌幫助你專注並吸收知識。',
    levels: [
      {
        name_en: 'Cardboard Box',
        name_zh: '紙箱桌',
        description_en: 'Not exactly ergonomic, but it works... barely.',
        description_zh: '不太符合人體工學，但勉強能用...',
        bonus: null,
      },
      {
        name_en: 'Folding Table',
        name_zh: '折疊桌',
        description_en: 'A simple folding table. At least it has legs!',
        description_zh: '一張簡單的折疊桌。至少它有腳！',
        bonus: { type: 'sparks', value: 0.5 },
      },
      {
        name_en: 'Wooden Desk',
        name_zh: '木質書桌',
        description_en: 'Solid oak craftsmanship. Now we\'re getting somewhere!',
        description_zh: '堅實的橡木工藝。現在我們有進步了！',
        bonus: { type: 'sparks', value: 1.0 },
      },
      {
        name_en: 'Executive Desk',
        name_zh: '高管書桌',
        description_en: 'Mahogany finish with brass accents. Very professional.',
        description_zh: '桃花心木飾面配黃銅裝飾。非常專業。',
        bonus: { type: 'sparks', value: 2.0 },
      },
      {
        name_en: 'Hover Desk',
        name_zh: '懸浮書桌',
        description_en: 'Antigravity technology! The desk of the future.',
        description_zh: '反重力技術！未來的書桌。',
        bonus: { type: 'sparks', value: 5.0 },
      },
    ],
  },
  lamp: {
    code: 'lamp',
    name_en: 'Desk Lamp',
    name_zh: '檯燈',
    description_en: 'Light up your studies! Good lighting reduces eye strain and keeps you alert.',
    description_zh: '照亮你的學習！良好的照明減少眼睛疲勞，讓你保持警覺。',
    levels: [
      {
        name_en: 'Bare Bulb',
        name_zh: '裸燈泡',
        description_en: 'Just a bulb dangling from a wire. Not pretty, but functional.',
        description_zh: '只是一顆燈泡掛在電線上。不漂亮，但能用。',
        bonus: null,
      },
      {
        name_en: 'Simple Lamp',
        name_zh: '簡易檯燈',
        description_en: 'A basic desk lamp with adjustable arm.',
        description_zh: '一盞有可調節臂的基本檯燈。',
        bonus: { type: 'essence', value: 0.5 },
      },
      {
        name_en: 'Fancy Lamp',
        name_zh: '精緻檯燈',
        description_en: 'Brass finish with adjustable brightness. Classy!',
        description_zh: '黃銅飾面，亮度可調。很有品味！',
        bonus: { type: 'essence', value: 1.5 },
      },
      {
        name_en: 'Magic Lamp',
        name_zh: '魔法燈',
        description_en: 'Glows with mystical energy. No genie, unfortunately.',
        description_zh: '散發神秘能量的光芒。很遺憾，沒有精靈。',
        bonus: { type: 'essence', value: 3.0 },
      },
    ],
  },
  chair: {
    code: 'chair',
    name_en: 'Chair',
    name_zh: '椅子',
    description_en: 'Comfort matters! A good chair supports long study sessions.',
    description_zh: '舒適很重要！一把好椅子支撐長時間的學習。',
    levels: [
      {
        name_en: 'Wooden Stool',
        name_zh: '木凳',
        description_en: 'Hard and unforgiving. Your back will complain.',
        description_zh: '又硬又無情。你的背會抱怨。',
        bonus: null,
      },
      {
        name_en: 'Office Chair',
        name_zh: '辦公椅',
        description_en: 'Padded seat with armrests. Much better!',
        description_zh: '有軟墊座椅和扶手。好多了！',
        bonus: { type: 'energy', value: 1.0 },
      },
      {
        name_en: 'Gaming Throne',
        name_zh: '電競王座',
        description_en: 'RGB lighting and supreme comfort. Ready for marathon sessions!',
        description_zh: 'RGB燈光和極致舒適。準備好馬拉松學習了！',
        bonus: { type: 'energy', value: 3.0 },
      },
    ],
  },
  bookshelf: {
    code: 'bookshelf',
    name_en: 'Bookshelf',
    name_zh: '書架',
    description_en: 'Store your knowledge! Books are the building blocks of wisdom.',
    description_zh: '儲存你的知識！書籍是智慧的基石。',
    levels: [
      {
        name_en: 'Cardboard Shelf',
        name_zh: '紙板架',
        description_en: 'Barely holds a few books. Don\'t sneeze near it.',
        description_zh: '勉強放幾本書。別在它旁邊打噴嚏。',
        bonus: null,
      },
      {
        name_en: 'Wooden Shelf',
        name_zh: '木質書架',
        description_en: 'A proper bookshelf. Now you can organize!',
        description_zh: '一個正式的書架。現在你可以整理了！',
        bonus: { type: 'blocks', value: 0.5 },
      },
      {
        name_en: 'Mahogany Case',
        name_zh: '桃花心木櫃',
        description_en: 'Elegant mahogany with glass doors. Very scholarly.',
        description_zh: '優雅的桃花心木配玻璃門。很有學者氣質。',
        bonus: { type: 'blocks', value: 1.5 },
      },
      {
        name_en: 'Grand Library',
        name_zh: '宏偉圖書館',
        description_en: 'Floor to ceiling books! You could get lost in here.',
        description_zh: '從地板到天花板都是書！你可能會迷失在這裡。',
        bonus: { type: 'blocks', value: 3.0 },
      },
    ],
  },
  sofa: {
    code: 'sofa',
    name_en: 'Sofa',
    name_zh: '沙發',
    description_en: 'Rest is important! A comfortable sofa for breaks and light reading.',
    description_zh: '休息很重要！一張舒適的沙發用於休息和輕鬆閱讀。',
    levels: [
      {
        name_en: 'Bean Bag',
        name_zh: '豆袋椅',
        description_en: 'Comfy but hard to get out of!',
        description_zh: '舒適但很難起來！',
        bonus: null,
      },
      {
        name_en: 'Leather Couch',
        name_zh: '皮沙發',
        description_en: 'Classic leather with wooden frame.',
        description_zh: '經典皮革配木框。',
        bonus: { type: 'sparks', value: 0.5 },
      },
      {
        name_en: 'Royal Divan',
        name_zh: '皇家躺椅',
        description_en: 'Velvet upholstery fit for royalty.',
        description_zh: '絲絨軟墊，適合皇室。',
        bonus: { type: 'sparks', value: 1.5 },
      },
      {
        name_en: 'Palace Throne',
        name_zh: '宮殿王座',
        description_en: 'Gold-trimmed magnificence. You ARE royalty now.',
        description_zh: '鍍金的華麗。你現在就是皇室了。',
        bonus: { type: 'sparks', value: 4.0 },
      },
    ],
  },
  tv: {
    code: 'tv',
    name_en: 'TV',
    name_zh: '電視',
    description_en: 'Entertainment and educational videos! Balance study with fun.',
    description_zh: '娛樂和教育視頻！學習與娛樂的平衡。',
    levels: [
      {
        name_en: 'Old CRT',
        name_zh: '老式映像管',
        description_en: 'Bulky and fuzzy, but nostalgic.',
        description_zh: '笨重又模糊，但很懷舊。',
        bonus: null,
      },
      {
        name_en: 'Flat Screen',
        name_zh: '平板電視',
        description_en: 'HD quality at last!',
        description_zh: '終於有高清畫質了！',
        bonus: { type: 'essence', value: 0.5 },
      },
      {
        name_en: 'Smart TV',
        name_zh: '智慧電視',
        description_en: '4K with streaming. So many learning videos!',
        description_zh: '4K串流。有這麼多學習視頻！',
        bonus: { type: 'essence', value: 1.0 },
      },
      {
        name_en: 'Home Cinema',
        name_zh: '家庭影院',
        description_en: 'Projector and surround sound. Immersive!',
        description_zh: '投影機和環繞音響。身臨其境！',
        bonus: { type: 'essence', value: 2.5 },
      },
    ],
  },
  plant: {
    code: 'plant',
    name_en: 'Plant',
    name_zh: '植物',
    description_en: 'Greenery improves mood and air quality! Nature in your room.',
    description_zh: '綠色植物改善心情和空氣質量！在你的房間裡有一點大自然。',
    levels: [
      {
        name_en: 'Seedling',
        name_zh: '幼苗',
        description_en: 'A tiny sprout. Handle with care!',
        description_zh: '一顆小芽。小心呵護！',
        bonus: null,
      },
      {
        name_en: 'Potted Plant',
        name_zh: '盆栽',
        description_en: 'A healthy houseplant. Looking green!',
        description_zh: '一株健康的室內植物。看起來很綠！',
        bonus: { type: 'blocks', value: 0.5 },
      },
      {
        name_en: 'Bonsai Tree',
        name_zh: '盆景',
        description_en: 'A carefully cultivated mini tree.',
        description_zh: '一棵精心培育的小樹。',
        bonus: { type: 'blocks', value: 1.0 },
      },
      {
        name_en: 'Indoor Garden',
        name_zh: '室內花園',
        description_en: 'A mini jungle! So refreshing.',
        description_zh: '一個小叢林！好清新。',
        bonus: { type: 'blocks', value: 2.0 },
      },
    ],
  },
  coffee_table: {
    code: 'coffee_table',
    name_en: 'Coffee Table',
    name_zh: '茶几',
    description_en: 'Perfect for snacks and drinks during study breaks.',
    description_zh: '學習休息時放零食和飲料的完美選擇。',
    levels: [
      {
        name_en: 'Crate Table',
        name_zh: '木箱桌',
        description_en: 'A wooden crate turned upside down. Resourceful!',
        description_zh: '一個倒過來的木箱。很有創意！',
        bonus: null,
      },
      {
        name_en: 'Glass Table',
        name_zh: '玻璃茶几',
        description_en: 'Sleek glass top with metal legs.',
        description_zh: '光滑的玻璃面配金屬腳。',
        bonus: { type: 'energy', value: 0.5 },
      },
      {
        name_en: 'Designer Table',
        name_zh: '設計師茶几',
        description_en: 'Artistic design that sparks joy.',
        description_zh: '藝術設計，帶來喜悅。',
        bonus: { type: 'energy', value: 1.5 },
      },
    ],
  },
}

// Helper to get bonus icon
export function getBonusIcon(type: BonusType): string {
  switch (type) {
    case 'sparks': return '✨'
    case 'energy': return '⚡'
    case 'essence': return '💧'
    case 'blocks': return '🧱'
  }
}

// Helper to get bonus color
export function getBonusColor(type: BonusType): string {
  switch (type) {
    case 'sparks': return 'text-yellow-400'
    case 'energy': return 'text-blue-400'
    case 'essence': return 'text-cyan-400'
    case 'blocks': return 'text-orange-400'
  }
}

// Get total bonus for an item at a specific level
export function getTotalBonus(code: string, level: number): ItemBonus | null {
  const config = ITEM_CONFIGS[code]
  if (!config || level <= 0) return null
  
  // Sum all bonuses up to current level
  let totalValue = 0
  let bonusType: BonusType | null = null
  
  for (let i = 1; i <= Math.min(level, config.levels.length - 1); i++) {
    const levelBonus = config.levels[i]?.bonus
    if (levelBonus) {
      bonusType = levelBonus.type
      totalValue += levelBonus.value
    }
  }
  
  if (bonusType && totalValue > 0) {
    return { type: bonusType, value: totalValue }
  }
  return null
}

