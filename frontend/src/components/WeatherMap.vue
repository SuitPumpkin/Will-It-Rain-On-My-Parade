<template>
  <div class="weather-dashboard">
    <div class="controls">
      <div class="search-container">
        <input
          type="text"
          placeholder="Search location"
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
        <button @click="clearPin">Clear pin</button>
        <select v-model="selectedDay">
          <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="selectedMonth">
          <option v-for="(m, index) in months" :key="index" :value="index">
            {{ m }}
          </option>
        </select>
        <button @click="fetchAllWeatherData" :disabled="isLoading">
          {{ isLoading ? "Searching..." : "Get Results" }}
        </button>
      </div>
    </div>

    <div class="main-content">
      <div id="map"></div>
      <div class="dashboard">
        <h2>Results Dashboard</h2>

        <div v-if="clickedCoordinates" class="coordinates-info">
          <h3>Selected Coordinates</h3>
          <div class="stat">
            <span>Latitude</span>
            <span class="value">{{ clickedCoordinates.lat.toFixed(4) }}</span>
          </div>
          <div class="stat">
            <span>Longitude</span>
            <span class="value">{{ clickedCoordinates.lng.toFixed(4) }}</span>
          </div>
          <button
            @click="fetchAllWeatherData"
            class="coords-button"
            :disabled="isLoading"
          >
            {{
              isLoading ? "Retrieving..." : "Get weather for these coordinates"
            }}
          </button>
        </div>

        <div v-if="weatherData || forecastData" class="view-toggle">
          <button
            :class="{ active: viewMode === 'forecast' }"
            @click="viewMode = 'forecast'"
          >
            Forecast
          </button>
          <button
            :class="{ active: viewMode === 'historical' }"
            @click="viewMode = 'historical'"
          >
            Historical
          </button>
        </div>

        <div v-if="isLoading" class="loading-indicator">Loading data...</div>

        <div v-if="viewMode === 'forecast' && forecastData && !isLoading">
          <div v-if="forecastData.status === 'unavailable'" class="coming-soon">
            <h3>Forecast Not Available</h3>
            <p>{{ forecastData.message }}</p>
          </div>
          <div v-else>
            <div class="main-day-view">
              <h3>Weather for {{ forecastData.main_day.date }}</h3>
              <div class="stat">
                <span>Max / Min Temp</span>
                <span class="value"
                  >{{ forecastData.main_day.max }}° /
                  {{ forecastData.main_day.min }}°C</span
                >
              </div>
              <div class="stat">
                <span>Rain Probability</span>
                <span class="value">{{ forecastData.main_day.rainProb }}%</span>
              </div>
            </div>
            <div class="forecast-view">
              <h4>Next 4 Days Forecast</h4>
              <div class="forecast-grid">
                <div
                  class="forecast-card"
                  v-for="day in forecastData.forecast"
                  :key="day.date"
                >
                  <span class="date">{{
                    new Date(day.date + "T00:00:00").toLocaleDateString(
                      "en-US",
                      { weekday: "short", day: "numeric" }
                    )
                  }}</span>
                  <span class="temps">{{ day.max }}°/{{ day.min }}°</span>
                  <span class="rain">💧 {{ day.rainProb }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="viewMode === 'historical' && weatherData && !isLoading">
          <div class="historical-summary">
            <h3>Historical Average (last 5 years)</h3>
            <div class="stat">
              <span>Average Temp (°C)</span
              ><span class="value">{{ weatherData.temp }}</span>
            </div>
            <div class="stat">
              <span>Min / Max Temp</span
              ><span class="value"
                >{{ weatherData.min }} / {{ weatherData.max }}</span
              >
            </div>
            <div class="stat">
              <span>Precipitation</span
              ><span class="value"
                >{{ weatherData.rain }} mm / {{ weatherData.rainProb }}%</span
              >
            </div>
          </div>
          <div v-if="historicalYearlyData.length > 0" class="historical-data">
            <h3>Detailed History</h3>
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
            <h3>Recommendations</h3>
            <ul>
              <li v-for="(rec, index) in recommendations" :key="index">
                {{ rec }}
              </li>
            </ul>
          </div>
        </div>

        <div v-if="!isLoading && !weatherData && !forecastData" class="no-data">
          Select a location to view weather data.
        </div>

        <h3>Temperature Chart (24h)</h3>
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

// --- REACTIVE STATES ---
const searchCity = ref("");
const selectedCity = ref("");
const selectedDay = ref(new Date().getDate().toString());
const selectedMonth = ref(new Date().getMonth().toString());
const clickedCoordinates = ref(null);
const isLoading = ref(false);
const viewMode = ref("forecast");
const weatherData = ref(null);
const forecastData = ref(null);
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
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const chartCanvas = ref(null);
let chartInstance = null;
let map = null;
let currentMarker = null;

// --- DATA LOGIC ---
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
      alert("City not found.");
      return;
    }
  } else if (clickedCoordinates.value) {
    lat = clickedCoordinates.value.lat;
    lon = clickedCoordinates.value.lng;
  } else {
    alert("Please select a city or a point on the map.");
    return;
  }

  isLoading.value = true;
  clearData();

  // --- NEW DATE CHECK LOGIC ---
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Normalize to midnight to compare only days
  const targetDate = new Date(selectedFullDate.value + "T00:00:00");
  const diffTime = targetDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  try {
    // The historical request is always made
    const historicalPromise = fetch(
      `http://127.0.0.1:8000/weather?lat=${lat}&lon=${lon}&day=${
        selectedDay.value
      }&month=${Number(selectedMonth.value) + 1}`
    );

    if (diffDays > 10) {
      // Case 1: Distant date. Only get history and force the view.
      viewMode.value = "historical";
      forecastData.value = {
        status: "unavailable",
        message:
          "Forecast not available for dates more than 10 days in advance.",
      };

      const historicalRes = await historicalPromise;
      if (historicalRes.ok) {
        const data = await historicalRes.json();
        weatherData.value = data.historical_summary;
        historicalYearlyData.value = data.historical_yearly_data;
        recommendations.value = data.recommendations;
      }
    } else {
      // Case 2: Near or past date. Get everything, default view is Forecast.
      viewMode.value = "forecast";
      const forecastPromise = fetch(
        `http://127.0.0.1:8000/forecast?lat=${lat}&lon=${lon}&date=${selectedFullDate.value}`
      );

      const [historicalRes, forecastRes] = await Promise.all([
        historicalPromise,
        forecastPromise,
      ]);

      if (historicalRes.ok) {
        const data = await historicalRes.json();
        weatherData.value = data.historical_summary;
        historicalYearlyData.value = data.historical_yearly_data;
        recommendations.value = data.recommendations;
      }
      if (forecastRes.ok) {
        forecastData.value = await forecastRes.json();
      }
    }
  } catch (error) {
    console.error("Error fetching data:", error);
    alert("An error occurred while fetching weather data.");
  }

  updateHourlyDataForChart();
  isLoading.value = false;

  if (currentMarker) map.removeLayer(currentMarker);
  currentMarker = L.marker([lat, lon])
    .addTo(map)
    .bindPopup(`<b>${selectedCity.value || "Selected location"}</b>`)
    .openPopup();
}

function updateHourlyDataForChart() {
  if (
    viewMode.value === "forecast" &&
    forecastData.value &&
    !forecastData.value.status
  ) {
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

// --- HELPER FUNCTIONS ---
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
  clickedCoordinates.value = null;
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
    selectedCity.value = "";
    searchCity.value = "";
    clearData();

    if (currentMarker) map.removeLayer(currentMarker);
    currentMarker = L.marker(e.latlng)
      .addTo(map)
      .bindPopup(
        `<b>Selected coordinates</b><br>Lat: ${e.latlng.lat.toFixed(
          4
        )}, Lng: ${e.latlng.lng.toFixed(4)}`
      )
      .openPopup();
  });

  try {
    const res = await fetch("/datasets/worldcities.json");
    allCities.value = await res.json();
  } catch (err) {
    console.error("Error loading cities:", err);
  }

  createChart();
});

onUnmounted(() => {
  if (chartInstance) chartInstance.destroy();
  if (map) map.remove();
});

// --- CHART LOGIC ---
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
          label: "Temperature per hour (°C)",
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
/* ... (all your existing styles go here, no need to copy them again) ... */
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
.historical-data h3 {
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
.coming-soon {
  background-color: #334155;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1rem;
  text-align: center;
  color: #94a3b8;
}
.coming-soon h3 {
  color: #f1f5f9;
  border-bottom: none;
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
