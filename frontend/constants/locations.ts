// constants/locations.ts - Location constants and utilities

export const REGIONS = [
  '北海道',
  '東北',
  '関東',
  '中部',
  '関西',
  '中国',
  '四国',
  '九州'
]

// Area name mapping for location classification
const AREA_MAPPINGS: Record<string, string> = {
  // 北海道
  '札幌': '北海道',
  '函館': '北海道',
  '旭川': '北海道',
  '釧路': '北海道',
  '帯広': '北海道',
  '網走': '北海道',
  '稚内': '北海道',
  '旧夷': '北海道',
  '北見': '北海道',
  '室蘭': '北海道',
  '苫小牧': '北海道',
  '更別': '北海道',
  '厚岸': '北海道',
  '弟子屈': '北海道',
  '標津': '北海道',
  '羅臼': '北海道',
  '根室': '北海道',
  '中標津': '北海道',
  '雄武': '北海道',
  '興部': '北海道',
  '遠別': '北海道',
  '東藻琴': '北海道',
  '中園別': '北海道',
  '高原': '北海道',
  '美深': '北海道',
  '利尻': '北海道',
  '鹿追': '北海道',
  '納沙布': '北海道',
  '毛綱': '北海道',
  '西興部': '北海道',
  '礼文': '北海道',
  '美幌': '北海道',
  '清水': '北海道',
  '小清水': '北海道',
  '大樹': '北海道',
  '美瑛': '北海道',
  '浦河': '北海道',
  '十勝': '北海道',
  '中札内': '北海道',
  
  // 東北
  '仙台': '東北',
  '盛岡': '東北',
  '秋田': '東北',
  '山形': '東北',
  '郡山': '東北',
  '福島': '東北',
  '青森': '東北',
  '岩手': '東北',
  '津軽': '東北',
  
  // 関東
  '東京': '関東',
  '横浜': '関東',
  '千葉': '関東',
  'さいたま': '関東',
  '水戸': '関東',
  '宇都宮': '関東',
  '前橋': '関東',
  '栃木': '関東',
  '父島': '関東',
  '小田原': '関東',
  '熊谷': '関東',
  '秩父': '関東',
  '銚子': '関東',
  '館山': '関東',
  '土浦': '関東',
  'みなかみ': '関東',
  
  // 中部
  '名古屋': '中部',
  '金沢': '中部',
  '富山': '中部',
  '長野': '中部',
  '新潟': '中部',
  '静岡': '中部',
  '岐阜': '中部',
  '福井': '中部',
  '甲府': '中部',
  '津': '中部',
  
  // 関西
  '大阪': '関西',
  '京都': '関西',
  '神戸': '関西',
  '奈良': '関西',
  '大津': '関西',
  '和歌山': '関西',
  // 中国
  '広島': '中国',
  '岡山': '中国',
  '鳥取': '中国',
  '島根': '中国',
  '山口': '中国',
  '松江': '中国',
  '雲南': '中国',
  '湯梨浜': '中国',
  '伯耆': '中国',
  '米子': '中国',
  
  // 四国
  '高松': '四国',
  '松山': '四国',
  '高知': '四国',
  '徳島': '四国',
  
  // 九州
  '福岡': '九州',
  '北九州': '九州',
  '佐賀': '九州',
  '長崎': '九州',
  '熊本': '九州',
  '大分': '九州',
  '宮崎': '九州',
  '鹿児島': '九州',
  '沖縄': '九州',
  '那覇': '九州',
  '西表島': '九州',
  '竹富': '九州',
  '石垣': '九州',
  '石垣島': '九州',
  '与那国': '九州',
  '波照間': '九州',
  '下地島': '九州'
}

/**
 * Get area name for a given location
 * @param locationName - Name of the location
 * @returns Area name or empty string if not found
 */
export const getAreaName = (locationName: string): string => {
  // Remove common suffixes for better matching
  const cleanName = locationName.replace(/[県市町村郡区]$/, '')
  
  // Try exact match first
  if (AREA_MAPPINGS[cleanName]) {
    return AREA_MAPPINGS[cleanName]
  }
  
  // Try partial match
  for (const [key, value] of Object.entries(AREA_MAPPINGS)) {
    if (cleanName.includes(key) || key.includes(cleanName)) {
      return value
    }
  }
  
  return ''
}

/**
 * Get all locations for a specific region
 * @param region - Region name
 * @returns Array of location names in that region
 */
export const getLocationsByRegion = (region: string): string[] => {
  return Object.entries(AREA_MAPPINGS)
    .filter(([_, area]) => area === region)
    .map(([location, _]) => location)
}

export default {
  REGIONS,
  getAreaName,
  getLocationsByRegion
}