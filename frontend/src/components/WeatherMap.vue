<template>
  <div class="weather-dashboard">
    <!-- Controles -->
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
        />
        <div
          v-if="showSuggestionsList && filteredCities.length > 0"
          class="suggestions"
        >
          <div
            v-for="(city, index) in filteredCities.slice(0, 8)"
            :key="city.city"
            class="suggestion-item"
            :class="{ selected: selectedSuggestionIndex === index }"
            @mousedown="selectCity(city)"
            @mouseenter="selectedSuggestionIndex = index"
          >
            <span class="city-name">{{ city.city }}</span>
            <span class="country-name">{{ city.country }}</span>
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
        <button @click="fetchAllWeatherData" :disabled="isLoading">
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
          <!-- BOTÓN RESTAURADO PARA BUSCAR DESDE COORDENADAS -->
          <button
            @click="fetchAllWeatherData"
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

        <!-- ***** NUEVO INTERRUPTOR DE VISTA ***** -->
        <div v-if="weatherData || forecastData" class="view-toggle">
          <button
            :class="{ active: viewMode === 'forecast' }"
            @click="viewMode = 'forecast'"
          >
            Pronóstico
          </button>
          <button
            :class="{ active: viewMode === 'historical' }"
            @click="viewMode = 'historical'"
          >
            Historial
          </button>
        </div>

        <div v-if="isLoading" class="loading-indicator">Cargando datos...</div>

        <!-- ***** VISTA DE PRONÓSTICO ***** -->
        <div v-if="viewMode === 'forecast' && forecastData && !isLoading">
          <div class="main-day-view">
            <h3>Clima para {{ forecastData.main_day.date }}</h3>
            <div class="stat">
              <span>Temp. Máx / Mín</span>
              <span class="value"
                >{{ forecastData.main_day.max }}° /
                {{ forecastData.main_day.min }}°C</span
              >
            </div>
            <div class="stat">
              <span>Prob. de Lluvia</span>
              <span class="value">{{ forecastData.main_day.rainProb }}%</span>
            </div>
          </div>
          <div class="forecast-view">
            <h4>Pronóstico Próximos 4 Días</h4>
            <div class="forecast-grid">
              <div
                class="forecast-card"
                v-for="day in forecastData.forecast"
                :key="day.date"
              >
                <span class="date">{{
                  new Date(day.date + "T00:00:00").toLocaleDateString("es-ES", {
                    weekday: "short",
                    day: "numeric",
                  })
                }}</span>
                <span class="temps">{{ day.max }}°/{{ day.min }}°</span>
                <span class="rain">💧 {{ day.rainProb }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ***** VISTA HISTÓRICA ***** -->
        <div v-if="viewMode === 'historical' && weatherData && !isLoading">
          <div class="historical-summary">
            <h3>Promedio Histórico (últimos 5 años)</h3>
            <div class="stat">
              <span>Temp. Promedio (°C)</span
              ><span class="value">{{ weatherData.temp }}</span>
            </div>
            <div class="stat">
              <span>Temp. Mín / Máx</span
              ><span class="value"
                >{{ weatherData.min }} / {{ weatherData.max }}</span
              >
            </div>
            <div class="stat">
              <span>Precipitación</span
              ><span class="value"
                >{{ weatherData.rain }} mm / {{ weatherData.rainProb }}%</span
              >
            </div>
          </div>
          <div v-if="historicalYearlyData.length > 0" class="historical-data">
            <h3>Historial Detallado</h3>
            <div
              class="stat"
              v-for="record in historicalYearlyData"
              :key="record.date"
            >
              <span>{{ record.date.split("-")[0] }}</span>
              <span class="value"
                >🌡️ {{ record.max }}° / {{ record.min }}° &nbsp; 💧
                {{ record.rainProb }}%</span
              >
            </div>
          </div>
          <div v-if="recommendations.length > 0" class="recommendations">
            <h3>Recomendaciones</h3>
            <ul>
              <li v-for="(rec, index) in recommendations" :key="index">
                {{ rec }}
              </li>
            </ul>
          </div>
        </div>

        <div v-if="!isLoading && !weatherData && !forecastData" class="no-data">
          Selecciona una ubicación para ver los datos.
        </div>

        <h3>Gráfico de Temperatura (24h)</h3>
        <div class="chart-container"><canvas ref="chartCanvas"></canvas></div>
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

const searchCity = ref("");
const selectedCity = ref("");
const selectedDay = ref(new Date().getDate().toString());
const selectedMonth = ref(new Date().getMonth().toString());
const clickedCoordinates = ref(null);
const isLoading = ref(false);

// Nuevos estados para las vistas
const viewMode = ref("forecast"); // Vista por defecto
const weatherData = ref(null); // Para datos históricos de NASA
const forecastData = ref(null); // Para datos de pronóstico de Open-Meteo
const recommendations = ref([]);
const historicalYearlyData = ref([]);
const hourlyData = ref(
  Array.from({ length: 24 }, (_, i) => ({ hour: `${i}:00`, temp: 0 }))
);

const allCities = ref([]);
const showSuggestionsList = ref(false);
const selectedSuggestionIndex = ref(-1);

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

const chartCanvas = ref(null);
let chartInstance = null;
let map = null;
let currentMarker = null;

// --- LÓGICA DE DATOS ---
const selectedFullDate = computed(() => {
  const year = new Date().getFullYear();
  const month = Number(selectedMonth.value);
  const day = Number(selectedDay.value);
  const date = new Date(year, month, day);
  return date.toISOString().split("T")[0];
});

async function fetchAllWeatherData() {
  let lat, lon;
  if (selectedCity.value) {
    const city = allCities.value.find((c) => c.city === selectedCity.value);
    if (city) {
      lat = city.lat;
      lon = city.lng;
      map.setView([lat, lon], 10);
    } else {
      alert("Ciudad no encontrada.");
      return;
    }
  } else if (clickedCoordinates.value) {
    lat = clickedCoordinates.value.lat;
    lon = clickedCoordinates.value.lng;
  } else {
    alert("Por favor, selecciona una ciudad o un punto en el mapa.");
    return;
  }

  isLoading.value = true;
  // Limpia solo los datos de clima, no la selección de coordenadas o ciudad
  weatherData.value = null;
  forecastData.value = null;
  historicalYearlyData.value = [];
  recommendations.value = [];

  // Llamadas a AMBOS endpoints en paralelo
  const [historicalRes, forecastRes] = await Promise.all([
    fetch(
      `http://127.0.0.1:8000/weather?lat=${lat}&lon=${lon}&day=${
        selectedDay.value
      }&month=${Number(selectedMonth.value) + 1}`
    ),
    fetch(
      `http://127.0.0.1:8000/forecast?lat=${lat}&lon=${lon}&date=${selectedFullDate.value}`
    ),
  ]);

  if (historicalRes.ok) {
    const data = await historicalRes.json();
    weatherData.value = data.historical_summary;
    historicalYearlyData.value = data.historical_yearly_data;
    recommendations.value = data.recommendations;
  }

  if (forecastRes.ok) {
    const data = await forecastRes.json();
    forecastData.value = data;
  }

  updateHourlyDataForChart();
  isLoading.value = false;

  if (currentMarker) map.removeLayer(currentMarker);
  currentMarker = L.marker([lat, lon])
    .addTo(map)
    .bindPopup(`<b>${selectedCity.value || "Ubicación seleccionada"}</b>`)
    .openPopup();
}

function updateHourlyDataForChart() {
  if (viewMode.value === "forecast" && forecastData.value) {
    hourlyData.value = forecastData.value.hourly_data;
  } else if (viewMode.value === "historical" && weatherData.value) {
    hourlyData.value = weatherData.value.hourly_data;
  } else {
    hourlyData.value = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      temp: 0,
    }));
  }
}

watch(viewMode, updateHourlyDataForChart);

//FUNCIONES AUXILIARES
const filteredCities = computed(() => {
  if (!searchCity.value.trim() || searchCity.value.length < 2) return [];
  const searchTerm = searchCity.value.toLowerCase();
  return allCities.value.filter(
    (city) =>
      city.city.toLowerCase().includes(searchTerm) ||
      city.country.toLowerCase().includes(searchTerm)
  );
});

function clearData() {
  weatherData.value = null;
  forecastData.value = null;
  historicalYearlyData.value = [];
  recommendations.value = [];
  hourlyData.value = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: 0,
  }));
}

function clearPin() {
  clearData();
  searchCity.value = "";
  selectedCity.value = "";
  clickedCoordinates.value = null;
  if (currentMarker) map.removeLayer(currentMarker);
}

const selectCity = (city) => {
  searchCity.value = `${city.city}, ${city.country}`;
  selectedCity.value = city.city;
  clickedCoordinates.value = null; // Limpiar click si se selecciona ciudad
  showSuggestionsList.value = false;
};

const onSearchInput = () => {
  showSuggestionsList.value = searchCity.value.length >= 2;
  selectedSuggestionIndex.value = -1;
};
const hideSuggestions = () => {
  setTimeout(() => {
    showSuggestionsList.value = false;
  }, 200);
};
const showSuggestions = () => {
  if (searchCity.value.length >= 2) showSuggestionsList.value = true;
};
const selectFirstSuggestion = () => {
  if (filteredCities.value.length > 0) {
    selectCity(filteredCities.value[0]);
  }
};

onMounted(async () => {
  map = L.map("map").setView([23.6345, -102.5528], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  map.on("click", (e) => {
    clickedCoordinates.value = e.latlng;
    selectedCity.value = ""; // Limpiar ciudad si se hace click
    searchCity.value = ""; // Limpiar texto de búsqueda
    clearData(); // Limpia los datos de clima anteriores

    if (currentMarker) map.removeLayer(currentMarker);
    // Coloca un pin temporal sin popup de datos
    currentMarker = L.marker(e.latlng)
      .addTo(map)
      .bindPopup(
        `<b>Coordenadas seleccionadas</b><br>Lat: ${e.latlng.lat.toFixed(
          4
        )}, Lng: ${e.latlng.lng.toFixed(4)}`
      )
      .openPopup();
  });

  try {
    const res = await fetch("/datasets/worldcities.json");
    allCities.value = await res.json();
  } catch (err) {
    console.error("Error al cargar ciudades:", err);
  }

  createChart();
});

onUnmounted(() => {
  if (chartInstance) chartInstance.destroy();
  if (map) map.remove();
});

//GRÁFICO
watch(
  hourlyData,
  (newData) => {
    if (chartInstance && newData && newData.length > 0) {
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
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#f1f5f9" } } },
      scales: {
        y: {
          grid: { color: "rgba(255,255,255,0.1)" },
          ticks: { color: "#f1f5f9" },
        },
        x: {
          grid: { color: "rgba(255,255,255,0.1)" },
          ticks: { color: "#f1f5f9" },
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
  font-family: "Segoe UI", sans-serif;
  background: #0f172a;
  color: white;
  padding: 1rem;
  min-height: 100vh;
}
.controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.search-container {
  position: relative;
  flex-grow: 1;
  min-width: 250px;
}
.controls-group {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.controls input,
.controls select,
.controls button {
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  border: none;
  font-size: 0.9rem;
  background: #1e293b;
  color: white;
  border: 1px solid #334155;
}
.controls button {
  background-color: #0ea5e9;
  cursor: pointer;
}
.controls button:disabled {
  background: #475569;
  cursor: not-allowed;
}
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
}
.suggestion-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
}
.suggestion-item:hover,
.suggestion-item.selected {
  background: #334155;
}
.main-content {
  display: flex;
  gap: 1rem;
  flex: 1;
  min-height: 500px;
}
#map {
  flex: 2;
  border-radius: 12px;
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
.stat {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #334155;
}
.stat .value {
  font-weight: 600;
  color: #0ea5e9;
}
.chart-container {
  min-height: 250px;
  flex: 1;
}
.no-data,
.loading-indicator {
  text-align: center;
  color: #94a3b8;
  padding: 2rem;
}
.recommendations,
.historical-data,
.main-day-view,
.forecast-view {
  background-color: #334155;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}
h3,
h4 {
  margin-top: 0;
  border-bottom: 1px solid #475569;
  padding-bottom: 0.5rem;
}
.recommendations ul {
  padding-left: 20px;
  margin: 0;
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

.coordinates-info {
  background: #334155;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
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

.view-toggle {
  display: flex;
  background-color: #1e293b;
  border-radius: 8px;
  border: 1px solid #334155;
  overflow: hidden;
}
.view-toggle button {
  flex: 1;
  padding: 0.75rem;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s, color 0.2s;
}
.view-toggle button.active {
  background-color: #0ea5e9;
  color: white;
  font-weight: 600;
}
.view-toggle button:not(.active):hover {
  background-color: #334155;
}

.forecast-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  text-align: center;
}
.forecast-card {
  background: #1e293b;
  border-radius: 8px;
  padding: 0.75rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.9rem;
}
.forecast-card .date {
  font-weight: 600;
  color: #cbd5e1;
}
.forecast-card .temps {
  font-weight: 500;
  font-size: 1.1rem;
}
.forecast-card .rain {
  color: #94a3b8;
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
}
</style>
