<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">🌤️ Pronostika</h1>
        <div class="mode-switcher">
          <span class="mode-label">{{
            isComplexMode ? "Expert Mode" : "Simple Mode"
          }}</span>
          <label class="switch">
            <input type="checkbox" v-model="isComplexMode" />
            <span class="slider"></span>
          </label>
        </div>
      </div>
      <p class="app-subtitle">
        {{
          isComplexMode
            ? "Advanced Weather Analytics & Forecasting"
            : "Simple weather checking for everyone!"
        }}
      </p>
    </header>

    <WeatherMap v-if="isComplexMode" />
    <WeatherMapSimple v-else />
  </div>
</template>

<script setup>
import { ref } from "vue";
import WeatherMap from "./components/WeatherMap.vue";
import WeatherMapSimple from "./components/WeatherMapSimple.vue";

const isComplexMode = ref(true);
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app {
  min-height: 100vh;
  background: #0f172a;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.app-header {
  background: #1e293b;
  padding: 1rem;
  border-bottom: 1px solid #334155;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.app-title {
  color: #f1f5f9;
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

.app-subtitle {
  color: #94a3b8;
  text-align: center;
  margin-top: 0.5rem;
  font-size: 1rem;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

/* Mode Switcher Styles */
.mode-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(30, 41, 59, 0.8);
  padding: 8px 16px;
  border-radius: 25px;
  border: 1px solid #475569;
}

.mode-label {
  color: #e2e8f0;
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
}

/* Switch styles */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #475569;
  transition: 0.3s;
  border-radius: 22px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #0ea5e9;
}

input:checked + .slider:before {
  transform: translateX(22px);
}

/* Responsive */
@media (max-width: 768px) {
  .app-header {
    padding: 0.75rem;
  }

  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .app-title {
    font-size: 1.5rem;
  }

  .mode-switcher {
    order: -1;
    margin-bottom: 0.5rem;
  }

  .app-subtitle {
    font-size: 0.9rem;
    margin-top: 0.25rem;
  }
}

@media (max-width: 480px) {
  .mode-switcher {
    padding: 6px 12px;
  }

  .mode-label {
    font-size: 0.8rem;
  }

  .switch {
    width: 40px;
    height: 20px;
  }

  .slider:before {
    height: 14px;
    width: 14px;
  }
}
</style>
