// Legacy component (kept for backwards compatibility)
export { StudyDesk, StudyDeskDemo } from './StudyDesk'

// New building system components
export { FurnitureItem, type ItemConfig, type FurnitureItemProps } from './FurnitureItem'
export { Room, type RoomProps, type RoomItem } from './Room'
export { RoomSwitcher, type RoomSwitcherProps } from './RoomSwitcher'
export { CurrencyBar, type CurrencyBarProps, type Currencies } from './CurrencyBar'
export { UpgradeModal, type UpgradeModalProps, type UpgradeCost, type UserCurrencies } from './UpgradeModal'
export { LevelUpModal, type LevelUpModalProps } from './LevelUpModal'
export { BlockMasteryAnimation, type BlockMasteryAnimationProps } from './BlockMasteryAnimation'
export { ItemDetailModal, type ItemDetailModalProps } from './ItemDetailModal'

// Item configuration
export { ITEM_CONFIGS, getTotalBonus, getBonusIcon, getBonusColor, type ItemBonus, type LevelDetail, type ItemFullConfig } from './itemConfig'
