<!-- WeatherData.vue component from src/tool_design/components/WeatherData.vue -->
<template>
  <div class="weather-data">
    <div class="component-header">
      <h3>天気データ入力</h3>
    </div>
    
    <div class="weather-content">
      <!-- Component implementation placeholder -->
      <p>天気データコンポーネント実装予定</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// Component logic will be implemented here
</script>

<style scoped>
.weather-data {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.component-header {
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid #6BA2FC;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.weather-content {
  padding: 2rem;
}
</style>