<template>
  <div class="weather-simple">
    <!-- Header Simple -->
    <div class="simple-header">
      <h1>🌤️ Will It Rain?</h1>
      <p>Find out if you need an umbrella! ☔</p>
    </div>

    <!-- Search Box -->
    <div class="simple-search">
      <div class="search-box">
        <input
          type="text"
          placeholder="Search for a city..."
          v-model="searchCity"
          @input="onSearchInput"
          @keyup.enter="selectFirstSuggestion"
        />
        <div
          v-if="showSuggestionsList && filteredCities.length > 0"
          class="suggestions"
        >
          <div
            v-for="city in filteredCities.slice(0, 5)"
            :key="city.city"
            class="suggestion-item"
            @mousedown="selectCity(city)"
          >
            <span class="city-name">{{ city.city }}</span>
            <span class="country-name">{{ city.country }}</span>
          </div>
        </div>
      </div>
      <button @click="fetchWeather" :disabled="isLoading" class="search-btn">
        {{ isLoading ? "🔍 Searching..." : "Check Weather" }}
      </button>
    </div>

    <!-- Date Selector -->
    <div class="date-selector">
      <label>📅 Which day are you traveling there?</label>
      <div class="date-inputs">
        <select v-model="selectedYear">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <select v-model="selectedMonth">
          <option
            v-for="(m, index) in simpleMonths"
            :key="index"
            :value="index"
          >
            {{ m }}
          </option>
        </select>
        <select v-model="selectedDay">
          <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
        </select>
      </div>
    </div>

    <!-- Map -->
    <div class="simple-map-container">
      <div id="simple-map"></div>
      <div class="map-instruction">
        💡 Click anywhere on the map to check weather there!
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="simple-loading">
      <div class="spinner"></div>
      <p>Checking the weather...</p>
    </div>

    <!-- Weather Results -->
    <div v-if="weatherResult && !isLoading" class="weather-result">
      <div class="result-card" :class="getWeatherClass()">
        <div class="weather-emoji">
          {{ getWeatherEmoji() }}
        </div>
        <div class="weather-info">
          <h3>{{ weatherResult.location }}</h3>
          <div class="weather-main">
            <div class="temperature">
              {{ getTemperature() }}
            </div>
            <div class="rain-info">
              {{ getRainInfo() }}
            </div>
          </div>
          <div class="recommendation">
            {{ getRecommendation() }}
          </div>
        </div>
      </div>

      <!-- Forecast for next days -->
      <div v-if="weatherResult.forecast" class="forecast-simple">
        <h4>Next few days:</h4>
        <div class="forecast-days">
          <div
            v-for="day in weatherResult.forecast.slice(0, 3)"
            :key="day.date"
            class="forecast-day"
          >
            <div class="day-name">{{ getDayName(day.date) }}</div>
            <div class="day-emoji">{{ getDayEmoji(day) }}</div>
            <div class="day-temp">{{ day.max }}°/{{ day.min }}°</div>
            <div class="day-rain">💧 {{ day.rainProb }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Data Message -->
    <div v-if="!weatherResult && !isLoading" class="no-data-simple">
      <div class="no-data-emoji">🗺️</div>
      <p>Search for a city or click on the map to check the weather!</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import L from "leaflet";

const searchCity = ref("");
const selectedCity = ref("");
const selectedYear = ref(new Date().getFullYear().toString());
const selectedMonth = ref(new Date().getMonth().toString());
const selectedDay = ref(new Date().getDate().toString());
const clickedCoordinates = ref(null);
const isLoading = ref(false);
const weatherResult = ref(null);

const allCities = ref([]);
const showSuggestionsList = ref(false);

// Generate years from current year to 5 years ago
const currentYear = new Date().getFullYear();
const years = Array.from({ length: 6 }, (_, i) => (currentYear - i).toString());

// Simple month names
const simpleMonths = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

const days = Array.from({ length: 31 }, (_, i) => (i + 1).toString());

let map = null;
let currentMarker = null;

// Función para validar coordenadas
function isValidCoordinate(lat, lng) {
  const validLat = lat >= -90 && lat <= 90;
  const validLng = lng >= -180 && lng <= 180;
  return validLat && validLng;
}

async function fetchWeather() {
  let lat, lon, locationName;

  if (selectedCity.value) {
    const city = allCities.value.find((c) => c.city === selectedCity.value);
    if (city) {
      lat = city.lat;
      lon = city.lng;
      locationName = `${city.city}, ${city.country}`;
      if (!isValidCoordinate(lat, lon)) {
        alert("Invalid city coordinates. Please select a different city.");
        return;
      }
      map.setView([lat, lon], 10);
    } else {
      alert("City not found. Please try another one.");
      return;
    }
  } else if (clickedCoordinates.value) {
    lat = clickedCoordinates.value.lat;
    lon = clickedCoordinates.value.lng;
    locationName = `Lat: ${lat.toFixed(2)}, Lng: ${lon.toFixed(2)}`;
    if (!isValidCoordinate(lat, lon)) {
      alert("Invalid coordinates. Please click on a valid location.");
      return;
    }
  } else {
    alert("Please search for a city or click on the map.");
    return;
  }

  isLoading.value = true;
  weatherResult.value = null;

  try {
    const forecastDate = new Date().toISOString().split("T")[0];

    const [historicalRes, forecastRes] = await Promise.all([
      fetch(
        `http://127.0.0.1:8000/weather?lat=${lat}&lon=${lon}&day=${
          selectedDay.value
        }&month=${Number(selectedMonth.value) + 1}&year=${selectedYear.value}`
      ),
      fetch(
        `http://127.0.0.1:8000/forecast?lat=${lat}&lon=${lon}&date=${forecastDate}`
      ),
    ]);

    let historicalData = null;
    let forecastData = null;

    if (historicalRes.ok) {
      const data = await historicalRes.json();
      historicalData = data.historical_summary;
    }

    if (forecastRes.ok) {
      const data = await forecastRes.json();
      forecastData = data;
    }

    // Combine data for simple display
    weatherResult.value = {
      location: locationName,
      historical: historicalData,
      forecast: forecastData?.forecast || [],
      mainDay: forecastData?.main_day,
    };
  } catch (error) {
    console.error("Error fetching weather:", error);
    alert("Oops! Couldn't get weather info. Please try again.");
  }

  isLoading.value = false;

  // Update map marker
  if (currentMarker) map.removeLayer(currentMarker);
  currentMarker = L.marker([lat, lon])
    .addTo(map)
    .bindPopup(`<b>${locationName}</b>`)
    .openPopup();
}

// Helper functions for display
function getWeatherClass() {
  if (!weatherResult.value?.mainDay) return "weather-unknown";

  const rainProb = weatherResult.value.mainDay.rainProb;
  if (rainProb > 70) return "weather-rainy";
  if (rainProb > 30) return "weather-cloudy";
  return "weather-sunny";
}

function getWeatherEmoji() {
  if (!weatherResult.value?.mainDay) return "❓";

  const rainProb = weatherResult.value.mainDay.rainProb;
  if (rainProb > 70) return "🌧️";
  if (rainProb > 30) return "🌤️";
  return "☀️";
}

function getTemperature() {
  if (!weatherResult.value?.mainDay) return "--°C";
  return `${weatherResult.value.mainDay.max}°C / ${weatherResult.value.mainDay.min}°C`;
}

function getRainInfo() {
  if (!weatherResult.value?.mainDay) return "No rain data";
  return `Rain chance: ${weatherResult.value.mainDay.rainProb}%`;
}

function getRecommendation() {
  if (!weatherResult.value?.mainDay) return "Check back later for updates!";

  const rainProb = weatherResult.value.mainDay.rainProb;
  if (rainProb > 70) return "🚨 Definitely bring an umbrella! ☔";
  if (rainProb > 40) return "🤔 You might need an umbrella";
  if (rainProb > 20) return "🌤️ Probably no umbrella needed";
  return "😎 Perfect weather! No umbrella needed";
}

function getDayName(dateString) {
  const date = new Date(dateString + "T00:00:00");
  return date.toLocaleDateString("en-US", { weekday: "short" });
}

function getDayEmoji(day) {
  if (day.rainProb > 70) return "🌧️";
  if (day.rainProb > 40) return "🌤️";
  return "☀️";
}

// Search functionality
const filteredCities = computed(() => {
  if (!searchCity.value.trim() || searchCity.value.length < 2) return [];
  const searchTerm = searchCity.value.toLowerCase();
  return allCities.value.filter(
    (city) =>
      city.city.toLowerCase().includes(searchTerm) ||
      city.country.toLowerCase().includes(searchTerm)
  );
});

const selectCity = (city) => {
  searchCity.value = `${city.city}, ${city.country}`;
  selectedCity.value = city.city;
  clickedCoordinates.value = null;
  showSuggestionsList.value = false;
};

const onSearchInput = () => {
  showSuggestionsList.value = searchCity.value.length >= 2;
};

const selectFirstSuggestion = () => {
  if (filteredCities.value.length > 0) {
    selectCity(filteredCities.value[0]);
  }
};

onMounted(async () => {
  // Simple map setup
  map = L.map("simple-map", {
    worldCopyJump: false,
    maxBounds: [
      [-90, -180],
      [90, 180],
    ],
    maxBoundsViscosity: 1.0,
  }).setView([23.6345, -102.5528], 3);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
    noWrap: true,
    bounds: [
      [-90, -180],
      [90, 180],
    ],
  }).addTo(map);

  map.on("click", (e) => {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    if (!isValidCoordinate(lat, lng)) {
      alert("Please click on a valid location on the map.");
      return;
    }

    clickedCoordinates.value = e.latlng;
    selectedCity.value = "";
    searchCity.value = "";
    weatherResult.value = null;

    if (currentMarker) map.removeLayer(currentMarker);
    currentMarker = L.marker(e.latlng)
      .addTo(map)
      .bindPopup(`<b>Selected Location</b>`)
      .openPopup();
  });

  try {
    const res = await fetch("/datasets/worldcities.json");
    allCities.value = await res.json();
  } catch (err) {
    console.error("Error loading cities:", err);
  }
});
</script>

<style scoped>
.weather-simple {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  min-height: calc(100vh - 120px);
  background: #0f172a;
  color: #f1f5f9;
}

.simple-header {
  text-align: center;
  margin-bottom: 30px;
  color: #f1f5f9;
}

.simple-header h1 {
  font-size: 2.5em;
  margin: 0;
  color: #f1f5f9;
}

.simple-header p {
  font-size: 1.2em;
  margin: 10px 0 0 0;
  color: #94a3b8;
}

.simple-search {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 250px;
}

.search-box input {
  width: 100%;
  padding: 15px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  background: #1e293b;
  color: #f1f5f9;
  border: 1px solid #334155;
}

.search-box input::placeholder {
  color: #64748b;
}

.search-box input:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
}

.search-btn {
  padding: 15px 25px;
  background: #0ea5e9;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #0ea5e9;
}

.search-btn:hover:not(:disabled) {
  background: #0284c7;
  transform: translateY(-1px);
}

.search-btn:disabled {
  background: #475569;
  border-color: #475569;
  cursor: not-allowed;
  transform: none;
}

.date-selector {
  background: #1e293b;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #334155;
}

.date-selector label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #f1f5f9;
}

.date-inputs {
  display: flex;
  gap: 10px;
}

.date-inputs select {
  flex: 1;
  padding: 10px;
  border: 1px solid #334155;
  border-radius: 6px;
  font-size: 16px;
  background: #0f172a;
  color: #f1f5f9;
  cursor: pointer;
}

.date-inputs select:focus {
  outline: none;
  border-color: #0ea5e9;
}

.simple-map-container {
  position: relative;
  margin-bottom: 20px;
}

#simple-map {
  height: 300px;
  border-radius: 8px;
  border: 1px solid #334155;
}

.map-instruction {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(30, 41, 59, 0.9);
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 14px;
  color: #cbd5e1;
  backdrop-filter: blur(10px);
  border: 1px solid #475569;
}

.simple-loading {
  text-align: center;
  padding: 40px;
  color: #cbd5e1;
}

.spinner {
  border: 4px solid rgba(100, 116, 139, 0.3);
  border-radius: 50%;
  border-top: 4px solid #0ea5e9;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.weather-result {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-card {
  background: #1e293b;
  border-radius: 8px;
  padding: 30px;
  margin-bottom: 20px;
  border: 1px solid #334155;
  display: flex;
  align-items: center;
  gap: 20px;
}

.weather-sunny {
  border-left: 6px solid #f59e0b;
}

.weather-cloudy {
  border-left: 6px solid #94a3b8;
}

.weather-rainy {
  border-left: 6px solid #0ea5e9;
}

.weather-unknown {
  border-left: 6px solid #64748b;
}

.weather-emoji {
  font-size: 4em;
  flex-shrink: 0;
}

.weather-info {
  flex: 1;
}

.weather-info h3 {
  margin: 0 0 15px 0;
  color: #f1f5f9;
  font-size: 1.5em;
}

.weather-main {
  margin-bottom: 15px;
}

.temperature {
  font-size: 2em;
  font-weight: bold;
  color: #f1f5f9;
  margin-bottom: 5px;
}

.rain-info {
  font-size: 1.2em;
  color: #cbd5e1;
}

.recommendation {
  font-size: 1.1em;
  font-weight: 600;
  padding: 10px 15px;
  background: #334155;
  border-radius: 6px;
  color: #f1f5f9;
  border: 1px solid #475569;
}

.weather-rainy .recommendation {
  background: #0c4a6e;
  border-color: #0ea5e9;
}

.weather-sunny .recommendation {
  background: #451a03;
  border-color: #f59e0b;
}

.forecast-simple {
  background: #1e293b;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #334155;
}

.forecast-simple h4 {
  margin: 0 0 15px 0;
  color: #f1f5f9;
}

.forecast-days {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.forecast-day {
  text-align: center;
  padding: 15px;
  background: #0f172a;
  border-radius: 6px;
  border: 1px solid #334155;
}

.day-name {
  font-weight: bold;
  margin-bottom: 8px;
  color: #f1f5f9;
}

.day-emoji {
  font-size: 2em;
  margin-bottom: 8px;
}

.day-temp {
  font-weight: bold;
  margin-bottom: 5px;
  color: #f1f5f9;
}

.day-rain {
  font-size: 0.9em;
  color: #94a3b8;
}

.no-data-simple {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.no-data-emoji {
  font-size: 4em;
  margin-bottom: 20px;
  opacity: 0.7;
}

.no-data-simple p {
  font-size: 1.2em;
  margin: 0;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #1e293b;
  border-radius: 0 0 8px 8px;
  border: 1px solid #334155;
  border-top: none;
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 12px 15px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #334155;
  color: #f1f5f9;
}

.suggestion-item:hover {
  background: #334155;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.city-name {
  font-weight: 600;
}

.country-name {
  color: #94a3b8;
  font-size: 0.9em;
}

@media (max-width: 768px) {
  .weather-simple {
    padding: 15px;
  }

  .simple-header h1 {
    font-size: 2em;
  }

  .simple-search {
    flex-direction: column;
  }

  .date-inputs {
    flex-direction: column;
  }

  .result-card {
    flex-direction: column;
    text-align: center;
    padding: 20px;
  }

  .weather-emoji {
    font-size: 3em;
  }

  .forecast-days {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
}
</style>
