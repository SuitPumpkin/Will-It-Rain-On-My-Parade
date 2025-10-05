<template>
  <div class="weather-dashboard">
    <div class="controls">
      <div class="search-container">
        <input
          type="text"
          placeholder="Buscar ubicación"
          v-model="searchCity"
          @input="onSearchInput"
          @keyup.enter="selectFirstSuggestion"
          @blur="hideSuggestions"
          @focus="showSuggestions"
          ref="searchInput"
        />
        <div
          v-if="showSuggestionsList && filteredCities.length > 0"
          class="suggestions"
        >
          <div
            v-for="(city, index) in filteredCities.slice(0, 8)"
            :key="`${city.city}-${city.country}-${index}`"
            class="suggestion-item"
            :class="{ selected: selectedSuggestionIndex === index }"
            @mousedown="selectCity(city)"
            @mouseenter="selectedSuggestionIndex = index"
          >
            <span class="city-name">{{ city.city }}</span>
            <span class="country-name">{{ city.country }}</span>
            <span class="coordinates"
              >({{ city.lat.toFixed(2) }}, {{ city.lng.toFixed(2) }})</span
            >
          </div>
        </div>
      </div>

      <div class="controls-group">
        <button @click="clearPin">Limpiar pin</button>

        <select v-model="selectedDay">
          <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="selectedMonth">
          <option v-for="(m, index) in months" :key="index" :value="index">
            {{ m }}
          </option>
        </select>

        <button @click="searchWeather" :disabled="isLoading">
          {{ isLoading ? "Buscando..." : "Obtener resultados" }}
        </button>
      </div>
    </div>

    <div class="main-content">
      <div id="map"></div>

      <div class="dashboard">
        <h2>Dashboard de Resultados</h2>

        <div v-if="clickedCoordinates" class="coordinates-info">
          <h3>Coordenadas seleccionadas</h3>
          <div class="stat">
            <span>Latitud</span>
            <span class="value">{{ clickedCoordinates.lat.toFixed(4) }}</span>
          </div>
          <div class="stat">
            <span>Longitud</span>
            <span class="value">{{ clickedCoordinates.lng.toFixed(4) }}</span>
          </div>
          <button
            @click="getWeatherForCoordinates"
            class="coords-button"
            :disabled="isLoading"
          >
            {{
              isLoading
                ? "Obteniendo..."
                : "Obtener clima para estas coordenadas"
            }}
          </button>
        </div>

        <div v-if="isLoading" class="loading-indicator">Cargando datos...</div>

        <div v-if="weatherData">
          <div class="stat">
            <span>Temp. Promedio (°C)</span>
            <span class="value">{{ weatherData.temp }}</span>
          </div>
          <div class="stat">
            <span>Temp. Mín / Máx Promedio</span>
            <span class="value"
              >{{ weatherData.min }} / {{ weatherData.max }}</span
            >
          </div>
          <div class="stat">
            <span>Precipitación Promedio</span>
            <span class="value"
              >{{ weatherData.rain }} mm / {{ weatherData.rainProb }}%</span
            >
          </div>
          <div class="stat">
            <span>Viento Promedio (km/h)</span>
            <span class="value">{{ weatherData.wind }}</span>
          </div>
        </div>

        <div v-else-if="!clickedCoordinates && !isLoading" class="no-data">
          Selecciona una ubicación para ver los datos meteorológicos
        </div>

        <div v-if="recommendations.length > 0" class="recommendations">
          <h3>Recomendaciones</h3>
          <ul>
            <li v-for="(rec, index) in recommendations" :key="index">
              {{ rec }}
            </li>
          </ul>
        </div>

        <div v-if="nearbyWeatherData.length > 0" class="nearby-weather">
          <h3>Clima en Zonas Cercanas (Actual)</h3>
          <div class="stat" v-for="loc in nearbyWeatherData" :key="loc.name">
            <span>{{ loc.name }}</span>
            <span class="value">{{ loc.temp }}°C / {{ loc.rainProb }}% 💧</span>
          </div>
        </div>

        <h3>Gráficos</h3>
        <div class="chart-container">
          <canvas ref="chartCanvas"></canvas>
        </div>
        <div v-if="historicalYearlyData.length > 0" class="historical-data">
          <h3>Historial (Misma Fecha)</h3>
          <div
            class="stat"
            v-for="record in historicalYearlyData"
            :key="record.date"
          >
            <span>{{ record.date.split("-")[0] }}</span>
            <span class="value">
              🌡️ {{ record.max }}° / {{ record.min }}°C &nbsp; 💧
              {{ record.rainProb }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from "vue";
import L from "leaflet";
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineController,
} from "chart.js";

// Registrar todos los componentes necesarios
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineController
);

// --- ESTADOS REACTIVOS ---
// Cerca de la línea 80
const recommendations = ref([]);
const nearbyWeatherData = ref([]);
const isLoading = ref(false);
const historicalYearlyData = ref([]); // <-- AÑADE ESTA LÍNEA
const searchCity = ref("");
const selectedCity = ref("");
const selectedDay = ref(new Date().getDate().toString());
const selectedMonth = ref(new Date().getMonth().toString());
const weatherData = ref(null);
const allCities = ref([]);
const hourlyData = ref(
  Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: 0,
  }))
);

// Estados para autocompletado
const showSuggestionsList = ref(false);
const selectedSuggestionIndex = ref(-1);
const searchInput = ref(null);

// Estado para coordenadas del doble click
const clickedCoordinates = ref(null);

// Arrays para los selectores
const days = Array.from({ length: 31 }, (_, i) => (i + 1).toString());
const months = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

// Computed para ciudades filtradas
const filteredCities = computed(() => {
  if (!searchCity.value.trim() || searchCity.value.length < 2) {
    return [];
  }
  const searchTerm = searchCity.value.toLowerCase();
  return allCities.value
    .filter(
      (city) =>
        city.city.toLowerCase().includes(searchTerm) ||
        city.country.toLowerCase().includes(searchTerm)
    )
    .slice(0, 15);
});

// Chart.js y Mapa
const chartCanvas = ref(null);
let chartInstance = null;
let map = null;
let currentMarker = null;
let clickMarker = null;

// --- FUNCIÓN PARA LLAMAR AL BACKEND ---
async function fetchWeatherDataFromAPI(lat, lon) {
  isLoading.value = true;
  weatherData.value = null;
  recommendations.value = [];
  nearbyWeatherData.value = [];

  const month = Number(selectedMonth.value) + 1;
  const day = selectedDay.value;

  try {
    const response = await fetch(
      `http://127.0.0.1:8000/weather?lat=${lat}&lon=${lon}&day=${day}&month=${month}`
    );
    if (!response.ok) {
      throw new Error("Error al obtener los datos del clima");
    }
    const data = await response.json();

    weatherData.value = data.historical_summary;
    hourlyData.value = data.historical_summary.hourly_data || [];
    recommendations.value = data.recommendations;
    nearbyWeatherData.value = data.nearby_locations;
    historicalYearlyData.value = data.historical_yearly_data;
  } catch (error) {
    console.error("Falló la llamada a la API:", error);
    alert(
      "No se pudieron obtener los datos del clima. Asegúrate de que el backend esté corriendo."
    );
    weatherData.value = null;
  } finally {
    isLoading.value = false;
  }
}

// --- FUNCIONES PARA OBTENER EL CLIMA ---
async function getWeatherForCoordinates() {
  if (!clickedCoordinates.value) return;
  const { lat, lng } = clickedCoordinates.value;

  if (currentMarker) map.removeLayer(currentMarker);

  await fetchWeatherDataFromAPI(lat, lng);

  if (weatherData.value) {
    currentMarker = L.marker([lat, lng])
      .addTo(map)
      .bindPopup(
        `
        <div style="color: #000;">
          <b>Coordenadas personalizadas</b><br>
          Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}<br>
          Temp. Promedio: ${weatherData.value.temp}°C<br>
          Mín/Máx Promedio: ${weatherData.value.min}°C / ${
          weatherData.value.max
        }°C<br>
          Viento Promedio: ${weatherData.value.wind} km/h
        </div>
      `
      )
      .openPopup();
  }
}

async function searchWeatherWithCity(city) {
  selectedCity.value = city.city;
  const coords = [city.lat, city.lng];

  map.setView(coords, 10);
  clearPin();

  await fetchWeatherDataFromAPI(coords[0], coords[1]);

  if (weatherData.value) {
    currentMarker = L.marker(coords)
      .addTo(map)
      .bindPopup(
        `
        <div style="color: #000;">
          <b>${selectedCity.value}</b><br>
          Temp. Promedio Hist.: ${weatherData.value.temp}°C<br>
          Mín/Máx: ${weatherData.value.min}°C / ${weatherData.value.max}°C<br>
          Viento: ${weatherData.value.wind} km/h
        </div>
      `
      )
      .openPopup();
  }
}

function searchWeather() {
  if (isLoading.value || !searchCity.value.trim()) return;

  if (selectedCity.value) {
    const city = allCities.value.find((c) => c.city === selectedCity.value);
    if (city) {
      searchWeatherWithCity(city);
      return;
    }
  }

  const city = allCities.value.find(
    (c) =>
      c.city.toLowerCase().includes(searchCity.value.toLowerCase()) ||
      `${c.city}, ${c.country}`
        .toLowerCase()
        .includes(searchCity.value.toLowerCase())
  );

  if (!city) {
    alert("Ciudad no encontrada. Intenta con otro nombre.");
    return;
  }
  searchWeatherWithCity(city);
}

// --- FUNCIONES AUXILIARES (Autocompletado, Mapa, Gráfico, etc.) ---
const onSearchInput = () => {
  showSuggestionsList.value = searchCity.value.length >= 2;
  selectedSuggestionIndex.value = -1;
};

const showSuggestions = () => {
  if (searchCity.value.length >= 2) showSuggestionsList.value = true;
};

const hideSuggestions = () => {
  setTimeout(() => {
    showSuggestionsList.value = false;
    selectedSuggestionIndex.value = -1;
  }, 200);
};

const selectCity = (city) => {
  searchCity.value = `${city.city}, ${city.country}`;
  selectedCity.value = city.city;
  showSuggestionsList.value = false;
  selectedSuggestionIndex.value = -1;
};

const selectFirstSuggestion = () => {
  if (filteredCities.value.length > 0 && showSuggestionsList.value) {
    if (selectedSuggestionIndex.value >= 0) {
      selectCity(filteredCities.value[selectedSuggestionIndex.value]);
    } else {
      selectCity(filteredCities.value[0]);
    }
  } else {
    searchWeather();
  }
};

const setupMapDoubleClick = () => {
  if (!map) return;
  map.on("click", (e) => {
    const { lat, lng } = e.latlng;
    clickedCoordinates.value = { lat, lng };
    if (clickMarker) map.removeLayer(clickMarker);
    clickMarker = L.marker([lat, lng])
      .addTo(map)
      .bindPopup(`<b>Coordenadas:</b><br>${lat.toFixed(4)}, ${lng.toFixed(4)}`)
      .openPopup();
    map.setView([lat, lng], map.getZoom());
    searchCity.value = "";
    selectedCity.value = "";
    weatherData.value = null;
    recommendations.value = [];
    nearbyWeatherData.value = [];
  });
};

const handleKeydown = (event) => {
  if (!showSuggestionsList.value) return;
  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      selectedSuggestionIndex.value =
        (selectedSuggestionIndex.value + 1) % filteredCities.value.length;
      break;
    case "ArrowUp":
      event.preventDefault();
      selectedSuggestionIndex.value =
        (selectedSuggestionIndex.value - 1 + filteredCities.value.length) %
        filteredCities.value.length;
      break;
    case "Enter":
      if (selectedSuggestionIndex.value >= 0) {
        event.preventDefault();
        selectCity(filteredCities.value[selectedSuggestionIndex.value]);
      }
      break;
    case "Escape":
      showSuggestionsList.value = false;
      selectedSuggestionIndex.value = -1;
      break;
  }
};

function clearPin() {
  if (currentMarker) map.removeLayer(currentMarker);
  if (clickMarker) map.removeLayer(clickMarker);
  currentMarker = null;
  clickMarker = null;
  weatherData.value = null;
  searchCity.value = "";
  selectedCity.value = "";
  showSuggestionsList.value = false;
  clickedCoordinates.value = null;
  recommendations.value = [];
  historicalYearlyData.value = [];
  nearbyWeatherData.value = [];
  hourlyData.value = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: 0,
  }));
}

// --- CICLO DE VIDA Y GRÁFICOS ---
onMounted(async () => {
  document.addEventListener("keydown", handleKeydown);

  map = L.map("map").setView([23.6345, -102.5528], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  setupMapDoubleClick();

  try {
    const res = await fetch("/datasets/worldcities.json");
    allCities.value = await res.json();
  } catch (err) {
    console.error("Error al cargar ciudades:", err);
    allCities.value = [
      {
        city: "Ciudad de México",
        lat: 19.4326,
        lng: -99.1332,
        country: "Mexico",
      },
    ]; // Fallback
  }

  createChart();
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
  if (chartInstance) chartInstance.destroy();
  if (map) map.remove();
});

watch(
  hourlyData,
  (newData) => {
    if (chartInstance && newData) {
      chartInstance.data.labels = newData.map((d) => d.hour);
      chartInstance.data.datasets[0].data = newData.map((d) => d.temp);
      chartInstance.update();
    }
  },
  { deep: true }
);

const createChart = () => {
  if (!chartCanvas.value) return;
  const ctx = chartCanvas.value.getContext("2d");
  if (chartInstance) chartInstance.destroy();
  chartInstance = new ChartJS(ctx, {
    type: "line",
    data: {
      labels: hourlyData.value.map((d) => d.hour),
      datasets: [
        {
          label: "Temperatura por hora (°C)",
          data: hourlyData.value.map((d) => d.temp),
          borderColor: "#4a90e2",
          backgroundColor: "rgba(74,144,226,0.2)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "top",
          labels: { color: "#f1f5f9" },
        },
        tooltip: {
          backgroundColor: "rgba(30, 41, 59, 0.95)",
          titleColor: "#f1f5f9",
          bodyColor: "#f1f5f9",
        },
      },
      scales: {
        y: {
          grid: { color: "rgba(255,255,255,0.1)" },
          ticks: { color: "#f1f5f9", callback: (value) => value + "°C" },
          title: { display: true, text: "Temperatura (°C)", color: "#f1f5f9" },
        },
        x: {
          grid: { color: "rgba(255,255,255,0.1)" },
          ticks: { color: "#f1f5f9" },
          title: { display: true, text: "Hora del día", color: "#f1f5f9" },
        },
      },
    },
  });
};
</script>

<style scoped>
.weather-dashboard {
  display: flex;
  flex-direction: column;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: #0f172a;
  color: white;
  padding: 1rem;
  min-height: 100vh;
}

.controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: nowrap;
  align-items: center;
  position: relative;
  justify-content: space-between;
}

.search-container {
  position: relative;
  flex: 0 0 300px; /* Ancho fijo para la búsqueda */
  min-width: 250px;
}

.controls-group {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex: 1;
}

.controls input,
.controls select,
.controls button {
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  border: none;
  font-size: 0.9rem;
  height: 38px;
  box-sizing: border-box;
}

.controls input {
  width: 100%;
  background: #1e293b;
  color: white;
  border: 1px solid #334155;
}

.controls input:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
}

.controls select {
  background: #1e293b;
  color: white;
  border: 1px solid #334155;
  min-width: 100px;
}

.controls button {
  background-color: #0ea5e9;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
  border: 1px solid #0284c7;
  white-space: nowrap;
}

.controls button:hover {
  background-color: #0284c7;
}

.controls button:disabled {
  background: #475569;
  cursor: not-allowed;
  border-color: #334155;
}

/* Estilos para las sugerencias */
.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  margin-top: 2px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.suggestion-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #334155;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.selected {
  background: #334155;
}

.city-name {
  font-weight: 600;
  color: #f1f5f9;
  flex: 1;
}

.country-name {
  color: #94a3b8;
  font-size: 0.875rem;
  margin: 0 0.5rem;
}

.coordinates {
  color: #64748b;
  font-size: 0.75rem;
  font-family: monospace;
}

/* Información de coordenadas */
.coordinates-info {
  background: #334155;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.coordinates-info h3 {
  margin: 0 0 0.75rem 0;
  color: #f1f5f9;
  font-size: 1.1rem;
}

.coords-button {
  width: 100%;
  background-color: #10b981;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background-color 0.3s;
}

.coords-button:hover {
  background-color: #059669;
}

.coords-button:disabled {
  background-color: #475569;
  cursor: not-allowed;
}

.main-content {
  display: flex;
  gap: 1rem;
  flex: 1;
  min-height: 500px;
}

#map {
  flex: 2;
  height: auto;
  border-radius: 12px;
  border: 1px solid #334155;
  cursor: pointer;
}

.dashboard {
  flex: 1;
  background: #1e293b;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-width: 320px;
  max-width: 450px;
  overflow-y: auto;
}

.dashboard h2,
.dashboard h3 {
  margin: 0;
  color: #f1f5f9;
}

.stat {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #334155;
  font-size: 0.95rem;
}

.stat:last-child {
  border-bottom: none;
}

.stat .value {
  font-weight: 600;
  color: #0ea5e9;
}

.no-data {
  text-align: center;
  color: #94a3b8;
  font-style: italic;
  padding: 2rem;
}

.chart-container {
  background: #0f172a;
  border-radius: 8px;
  padding: 1rem;
  position: relative;
  flex: 1;
  min-height: 250px;
}

canvas {
  width: 100% !important;
  height: 100% !important;
}

.loading-indicator {
  text-align: center;
  padding: 2rem;
  font-style: italic;
  color: #94a3b8;
}

.recommendations,
.nearby-weather {
  background-color: #334155;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.recommendations h3,
.nearby-weather h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #f1f5f9;
  border-bottom: 1px solid #475569;
  padding-bottom: 0.5rem;
  font-size: 1.1rem;
}

.recommendations ul {
  padding-left: 20px;
  margin: 0;
}

.recommendations li {
  margin-bottom: 0.5rem;
  color: #cbd5e1;
}

@media (max-width: 1024px) {
  .controls {
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .search-container {
    flex: 1 1 100%;
    min-width: auto;
  }

  .controls-group {
    flex: 1 1 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  #map {
    height: 350px;
    flex-grow: 0;
  }
  .dashboard {
    max-width: 100%;
  }
  .historical-data {
    background-color: #334155;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
  }

  .historical-data h3 {
    margin-top: 0;
    margin-bottom: 0.75rem;
    color: #f1f5f9;
    border-bottom: 1px solid #475569;
    padding-bottom: 0.5rem;
    font-size: 1.1rem;
  }
}
</style>
