<template>
  <div class="weather-simple">
    <div class="simple-header">
      <h1>🌤️ Weather Checker</h1>
      <p>Your simple view for past and future weather! ☔</p>
    </div>

    <div class="simple-search">
      <div class="search-box">
        <input
          type="text"
          placeholder="Search for a city..."
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
    </div>

    <div class="date-selector">
      <label>📅 Select a date</label>
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

    <button @click="fetchWeather" :disabled="isLoading" class="search-btn">
      {{ isLoading ? "🔍 Searching..." : "Check Weather" }}
    </button>

    <div class="simple-map-container">
      <div id="simple-map"></div>
      <div class="map-instruction">💡 Or click anywhere on the map!</div>
    </div>

    <div v-if="isLoading" class="simple-loading">
      <div class="spinner"></div>
      <p>Checking the skies...</p>
    </div>

    <div v-if="weatherResult && !isLoading" class="weather-result">
      <div v-if="displayCardData" class="result-card" :class="weatherClass">
        <div class="weather-emoji">
          {{ weatherEmoji }}
        </div>
        <div class="weather-info">
          <h3>{{ weatherResult.location }}</h3>
          <h4 class="data-subtitle">{{ dataSubtitle }}</h4>
          <div class="weather-main">
            <div class="temperature">
              {{ temperatureText }}
            </div>
            <div class="rain-info">
              {{ rainInfoText }}
            </div>
          </div>
          <div v-if="recommendationText" class="recommendation">
            {{ recommendationText }}
          </div>
        </div>
      </div>

      <div
        v-if="
          !isFutureDate &&
          weatherResult.forecast &&
          weatherResult.forecast.length > 0
        "
        class="forecast-simple"
      >
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

    <div v-if="!weatherResult && !isLoading" class="no-data-simple">
      <div class="no-data-emoji">🗺️</div>
      <p>Search for a city or click on the map to check the weather!</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import L from "leaflet";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

const searchCity = ref("");
const selectedCity = ref("");
const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear.toString());
const selectedMonth = ref(new Date().getMonth().toString());
const selectedDay = ref(new Date().getDate().toString());
const clickedCoordinates = ref(null);
const isLoading = ref(false);
const weatherResult = ref(null);

const allCities = ref([]);
const showSuggestionsList = ref(false);

const years = Array.from({ length: 33 }, (_, i) =>
  (currentYear + 1 - i).toString()
);
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

function isValidCoordinate(lat, lng) {
  return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
}

async function fetchWeather() {
  let lat, lon, locationName;

  if (selectedCity.value) {
    const city = allCities.value.find((c) => c.city === selectedCity.value);
    if (city) {
      lat = city.lat;
      lon = city.lng;
      locationName = `${city.city}, ${city.country}`;
      map.setView([lat, lon], 10);
    } else {
      alert("City not found. Please try another one.");
      return;
    }
  } else if (clickedCoordinates.value) {
    lat = clickedCoordinates.value.lat;
    lon = clickedCoordinates.value.lng;
    locationName = `Lat: ${lat.toFixed(2)}, Lng: ${lon.toFixed(2)}`;
  } else {
    alert("Please search for a city or click on the map.");
    return;
  }

  if (!isValidCoordinate(lat, lon)) {
    alert("Invalid coordinates selected.");
    return;
  }

  isLoading.value = true;
  weatherResult.value = null;

  try {
    const formattedDate = `${selectedYear.value}-${String(
      Number(selectedMonth.value) + 1
    ).padStart(2, "0")}-${String(selectedDay.value).padStart(2, "0")}`;

    const [historicalRes, forecastRes] = await Promise.all([
      fetch(
        `http://127.0.0.1:8000/weather?lat=${lat}&lon=${lon}&day=${
          selectedDay.value
        }&month=${Number(selectedMonth.value) + 1}&year=${selectedYear.value}`
      ),
      fetch(
        `http://127.0.0.1:8000/forecast?lat=${lat}&lon=${lon}&date=${formattedDate}`
      ),
    ]);

    const historicalData = historicalRes.ok ? await historicalRes.json() : null;
    const forecastData = forecastRes.ok ? await forecastRes.json() : null;

    if (forecastData?.status === "unavailable") {
      weatherResult.value = {
        location: locationName,
        historical: historicalData?.historical_summary,
        recommendations: historicalData?.recommendations || [],
      };
    } else {
      weatherResult.value = {
        location: locationName,
        historical: historicalData?.historical_summary,
        forecast: forecastData?.forecast || [],
        mainDay: forecastData?.main_day,
        recommendations: historicalData?.recommendations || [],
      };
    }
  } catch (error) {
    console.error("Error fetching weather:", error);
    alert("Oops! Couldn't get weather info. Please try again.");
  }

  isLoading.value = false;

  if (currentMarker) map.removeLayer(currentMarker);
  currentMarker = L.marker([lat, lon])
    .addTo(map)
    .bindPopup(`<b>${locationName}</b>`)
    .openPopup();
}

// --- Propiedades Computadas para la Visualización ---

const isFutureDate = computed(() => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const targetDateStr = `${selectedYear.value}-${
    Number(selectedMonth.value) + 1
  }-${selectedDay.value}`;
  const targetDate = new Date(targetDateStr);
  return targetDate > today;
});

const displayCardData = computed(() => {
  if (!weatherResult.value) return null;
  if (isFutureDate.value) {
    return weatherResult.value.historical;
  }
  return weatherResult.value.mainDay;
});

const dataSubtitle = computed(() => {
  if (!displayCardData.value) return "";
  return isFutureDate.value
    ? "Based on 5-year historical average"
    : `Data for ${displayCardData.value.date}`;
});

const weatherClass = computed(() => {
  if (!displayCardData.value) return "weather-unknown";
  const { rainProb } = displayCardData.value;
  if (rainProb > 70) return "weather-rainy";
  if (rainProb > 30) return "weather-cloudy";
  return "weather-sunny";
});

// --- LÓGICA DE EMOJI CORREGIDA ---
const weatherEmoji = computed(() => {
  if (!displayCardData.value) return "❓";
  const { rainProb, max } = displayCardData.value;

  if (rainProb > 70) return "🌧️";
  if (rainProb > 40) return "🌦️";

  // Nueva Lógica: Si hace mucho frío, muestra un emoji de frío.
  if (max < 5) return "🥶";

  if (rainProb > 20) return "🌤️";
  return "☀️";
});

const temperatureText = computed(() => {
  if (!displayCardData.value) return "--° / --°C";
  return `${displayCardData.value.max}° / ${displayCardData.value.min}°C`;
});

const rainInfoText = computed(() => {
  if (!displayCardData.value) return "No data";
  return `Rain Chance: ${displayCardData.value.rainProb}%`;
});

const recommendationText = computed(() => {
  return weatherResult.value?.recommendations?.[0] || "Enjoy your day!";
});

function getDayName(dateString) {
  return new Date(dateString + "T00:00:00").toLocaleDateString("en-US", {
    weekday: "short",
  });
}

// --- LÓGICA DE EMOJI CORREGIDA ---
function getDayEmoji(day) {
  if (day.rainProb > 70) return "🌧️";
  if (day.rainProb > 40) return "🌦️";

  // Nueva Lógica: Si hace mucho frío, muestra un emoji de frío.
  if (day.max < 5) return "🥶";

  if (day.rainProb > 20) return "🌤️";
  return "☀️";
}

// --- Funcionalidad de Búsqueda ---
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
  }).addTo(map);

  map.on("click", (e) => {
    if (!isValidCoordinate(e.latlng.lat, e.latlng.lng)) return;
    clickedCoordinates.value = e.latlng;
    selectedCity.value = "";
    searchCity.value = "";
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
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  font-family: "Segoe UI", sans-serif;
  background: #0f172a;
  color: #f1f5f9;
  border-radius: 12px;
}
.simple-header {
  text-align: center;
  margin-bottom: 30px;
}
.simple-header h1 {
  font-size: 2.5em;
  margin: 0;
}
.simple-header p {
  font-size: 1.2em;
  margin: 10px 0 0;
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
  min-width: 200px;
}
.search-box input {
  width: 100%;
  padding: 12px;
  border: 1px solid #334155;
  border-radius: 8px;
  font-size: 1em;
  background: #1e293b;
  color: #f1f5f9;
}
.search-btn {
  display: block;
  width: 100%;
  margin-top: 20px;
  padding: 15px;
  background: #0ea5e9;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.search-btn:hover:not(:disabled) {
  background: #0284c7;
}
.search-btn:disabled {
  background: #475569;
  cursor: not-allowed;
}
.date-selector {
  background: #1e293b;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
  border: 1px solid #334155;
}
.date-selector label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
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
  font-size: 1em;
  background: #0f172a;
  color: #f1f5f9;
}
#simple-map {
  height: 250px;
  border-radius: 8px;
  border: 1px solid #334155;
  margin-bottom: 5px;
}
.map-instruction {
  text-align: center;
  font-size: 0.9em;
  color: #94a3b8;
  margin-bottom: 20px;
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
  margin: 0 auto 15px;
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
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.result-card {
  background: #1e293b;
  border-radius: 8px;
  padding: 25px;
  margin-bottom: 20px;
  border-left: 5px solid #64748b;
  display: flex;
  align-items: center;
  gap: 20px;
}
.weather-sunny {
  border-color: #f59e0b;
}
.weather-cloudy {
  border-color: #94a3b8;
}
.weather-rainy {
  border-color: #0ea5e9;
}
.weather-info h3 {
  margin: 0 0 5px 0;
  font-size: 1.4em;
}
.weather-info h4.data-subtitle {
  font-size: 0.9em;
  color: #94a3b8;
  margin: 0 0 10px;
  font-weight: 400;
}
.weather-emoji {
  font-size: 3.5em;
}
.temperature {
  font-size: 1.8em;
  font-weight: bold;
}
.rain-info {
  font-size: 1.1em;
  color: #cbd5e1;
  margin-top: 5px;
}
.recommendation {
  font-size: 1em;
  font-weight: 500;
  margin-top: 15px;
  padding: 10px;
  background: #334155;
  border-radius: 6px;
}
.forecast-simple {
  background: #1e293b;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #334155;
}
.forecast-simple h4 {
  margin: 0 0 15px 0;
}
.forecast-days {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.forecast-day {
  text-align: center;
  padding: 10px;
  background: #0f172a;
  border-radius: 6px;
}
.day-name {
  font-weight: bold;
}
.day-emoji {
  font-size: 1.8em;
  margin: 5px 0;
}
.day-temp {
  font-weight: bold;
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
}
.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #1e293b;
  border-radius: 0 0 8px 8px;
  border: 1px solid #334155;
  z-index: 1000;
}
.suggestion-item {
  padding: 12px 15px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #334155;
}
.suggestion-item:hover {
  background: #334155;
}
.suggestion-item:last-child {
  border-bottom: none;
}
</style>
