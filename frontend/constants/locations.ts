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
  
  // 東北
  '仙台': '東北',
  '盛岡': '東北',
  '秋田': '東北',
  '山形': '東北',
  '郡山': '東北',
  '福島': '東北',
  '青森': '東北',
  '岩手': '東北',
  
  // 関東
  '東京': '関東',
  '横浜': '関東',
  '千葉': '関東',
  'さいたま': '関東',
  '水戸': '関東',
  '宇都宮': '関東',
  '前橋': '関東',
  '
  // 中部
  '名古屋': '中部',
  '金沢': '中部',
  '富山': '中部',
  '長野': '中部',
  '新潟': '中部',
  '静岡': '中部',
  '岐阜': '中部',
  '福井': '中部',
  
  // 関西
  '大阪': '関西',
  '京都': '関西',
  '神戸': '関西',
  '奈良': '関西',
  '大津': '関西',
  '和歌山': '関西',
  '
  // 中国
  '広島': '中国',
  '岡山': '中国',
  '鳥取': '中国',
  '島根': '中国',
  '山口': '中国',
  
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
  '沖縄': '九州'
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