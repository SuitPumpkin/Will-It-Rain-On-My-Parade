<template>
  <div class="app">
    <header class="app-header">
      <h1 class="app-title">🌤️ Pronostika</h1>
    </header>
    <WeatherMap />
  </div>
</template>

<script setup>
import WeatherMap from "./components/WeatherMap.vue";
import { onMounted } from "vue";

// Establecer el título de la ventana
onMounted(() => {
  document.title = "Pronostika - Pronóstico Meteorológico";
});
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
  text-align: center;
}

.app-title {
  color: #f1f5f9;
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .app-header {
    padding: 0.75rem;
  }

  .app-title {
    font-size: 1.5rem;
  }
}
</style>
