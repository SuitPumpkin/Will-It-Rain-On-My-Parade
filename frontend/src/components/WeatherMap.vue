<template>
  <div class="weather-dashboard">
    <div class="controls">
      <div class="search-container">
        <input
          type="text"
          placeholder="Search city..."
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
        <select v-model="selectedYear">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <select v-model="selectedMonth">
          <option v-for="(m, index) in months" :key="index" :value="index">
            {{ m }}
          </option>
        </select>
        <select v-model="selectedDay">
          <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
        </select>
        <button @click="fetchAllWeatherData" :disabled="isLoading">
          {{ isLoading ? "Searching..." : "Get Results" }}
        </button>
        <div class="dropdown">
          <button
            class="download-btn"
            :disabled="!hasDataToDownload || isLoading"
          >
            📥 Download
          </button>
          <div class="dropdown-content">
            <a href="#" @click.prevent="downloadData('pdf')">PDF</a>
            <a href="#" @click.prevent="downloadData('csv')">CSV</a>
            <a href="#" @click.prevent="downloadData('json')">JSON</a>
            <a href="#" @click.prevent="downloadData('jpg')">JPG Image</a>
          </div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div id="map"></div>
      <div class="dashboard">
        <h2>Result Dashboard</h2>
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
              isLoading ? "Retrieving..." : "Get Weather for These Coordinates"
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

        <div v-if="isLoading" class="loading-indicator">Loading Data...</div>

        <div v-if="viewMode === 'forecast' && forecastData && !isLoading">
          <div class="main-day-view">
            <h3>Weather for {{ forecastData.main_day.date }}</h3>
            <div class="stat">
              <span>Max / Min Temp.</span>
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
                  new Date(day.date + "T00:00:00").toLocaleDateString("en-US", {
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

        <div v-if="viewMode === 'historical' && weatherData && !isLoading">
          <div class="historical-summary">
            <h3>Historical Average (Last 5 Years)</h3>
            <div class="stat">
              <span>Average Temp. (°C)</span>
              <span class="value">{{ weatherData.temp }}</span>
            </div>
            <div class="stat">
              <span>Min / Max Temp.</span>
              <span class="value"
                >{{ weatherData.min }}° / {{ weatherData.max }}°C</span
              >
            </div>
            <div class="stat">
              <span>Precipitation</span>
              <span class="value"
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
          Click on the map or search for a city to get weather information.
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

const searchCity = ref("");
const selectedCity = ref("");
const selectedYear = ref(new Date().getFullYear().toString());
const selectedMonth = ref(new Date().getMonth().toString());
const selectedDay = ref(new Date().getDate().toString());
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

// Generate years from current year to 5 years ago
const currentYear = new Date().getFullYear();
const years = Array.from({ length: 6 }, (_, i) => (currentYear - i).toString());

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

// Función para validar coordenadas
function isValidCoordinate(lat, lng) {
  // Coordenadas válidas están entre estos rangos
  const validLat = lat >= -90 && lat <= 90;
  const validLng = lng >= -180 && lng <= 180;

  return validLat && validLng;
}

async function fetchAllWeatherData() {
  let lat, lon;
  if (selectedCity.value) {
    const city = allCities.value.find((c) => c.city === selectedCity.value);
    if (city) {
      lat = city.lat;
      lon = city.lng;
      // Validar coordenadas de la ciudad
      if (!isValidCoordinate(lat, lon)) {
        alert("Invalid city coordinates. Please select a different city.");
        return;
      }
      map.setView([lat, lon], 10);
    } else {
      alert("City not found.");
      return;
    }
  } else if (clickedCoordinates.value) {
    lat = clickedCoordinates.value.lat;
    lon = clickedCoordinates.value.lng;
    // Validar coordenadas del click
    if (!isValidCoordinate(lat, lon)) {
      alert(
        "Invalid coordinates. Please click on a valid location on the map."
      );
      return;
    }
  } else {
    alert("Please search for a city or click on the map.");
    return;
  }

  isLoading.value = true;
  weatherData.value = null;
  forecastData.value = null;
  historicalYearlyData.value = [];
  recommendations.value = [];

  // For forecast, use current date; for historical, use selected date
  const forecastDate = new Date().toISOString().split("T")[0];

  try {
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
  } catch (error) {
    console.error("Error fetching weather data:", error);
    alert("Error fetching weather data. Please try again.");
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
  // Configurar el mapa sin wrap-around y con límites mundiales
  map = L.map("map", {
    worldCopyJump: false, // Evita saltar entre copias del mundo
    maxBounds: [
      [-90, -180], // Esquina suroeste
      [90, 180], // Esquina noreste
    ],
    maxBoundsViscosity: 1.0, // Fuerza los límites estrictamente
  }).setView([23.6345, -102.5528], 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
    noWrap: true, // Evita que los tiles se repitan
    bounds: [
      [-90, -180],
      [90, 180],
    ],
  }).addTo(map);

  // Agregar control de escala para mejor UX
  L.control.scale().addTo(map);

  map.on("click", (e) => {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // Validar coordenadas antes de aceptarlas
    if (!isValidCoordinate(lat, lng)) {
      alert(
        "Invalid coordinates. Please click on a valid location on the map."
      );
      return;
    }

    clickedCoordinates.value = e.latlng;
    selectedCity.value = "";
    searchCity.value = "";
    clearData();

    if (currentMarker) map.removeLayer(currentMarker);
    currentMarker = L.marker(e.latlng)
      .addTo(map)
      .bindPopup(
        `<b>Selected Coordinates</b><br>Lat: ${lat.toFixed(
          4
        )}, Lng: ${lng.toFixed(4)}`
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
          label: "Temperature by hour (°C)",
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

const hasDataToDownload = computed(() => {
  return weatherData.value || forecastData.value;
});

const downloadData = async (format) => {
  if (!hasDataToDownload.value) {
    alert("No data available for download");
    return;
  }

  try {
    switch (format) {
      case "pdf":
        await downloadPDF();
        break;
      case "csv":
        downloadCSV();
        break;
      case "json":
        downloadJSON();
        break;
      case "jpg":
        await downloadJPG();
        break;
    }
  } catch (error) {
    console.error("Error downloading:", error);
    alert("Error generating file");
  }
};

const downloadPDF = async () => {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF();

  let yPosition = 20;
  const addText = (text, x = 20, fontSize = 12, isBold = false) => {
    doc.setFontSize(fontSize);
    doc.setFont(undefined, isBold ? "bold" : "normal");
    doc.text(text, x, yPosition);
    yPosition += 10;
  };

  addText("Weather Report", 20, 16, true);
  yPosition += 5;

  if (selectedCity.value) {
    addText(`City: ${selectedCity.value}`);
  }
  if (clickedCoordinates.value) {
    addText(
      `Coordinates: ${clickedCoordinates.value.lat.toFixed(
        4
      )}, ${clickedCoordinates.value.lng.toFixed(4)}`
    );
  }
  addText(
    `Date: ${selectedYear.value}-${String(
      Number(selectedMonth.value) + 1
    ).padStart(2, "0")}-${selectedDay.value.padStart(2, "0")}`
  );
  yPosition += 10;

  if (viewMode.value === "forecast" && forecastData.value) {
    addText("FORECAST DATA", 20, 14, true);
    addText(`Main Day: ${forecastData.value.main_day.date}`);
    addText(
      `Temperature: ${forecastData.value.main_day.max}° / ${forecastData.value.main_day.min}°C`
    );
    addText(`Rain Probability: ${forecastData.value.main_day.rainProb}%`);
    yPosition += 5;

    addText("Next 4 Days:", 20, 12, true);
    forecastData.value.forecast.forEach((day) => {
      addText(
        `${day.date}: ${day.max}°/${day.min}°C, Rain: ${day.rainProb}%`,
        25
      );
    });
  } else if (viewMode.value === "historical" && weatherData.value) {
    addText("HISTORICAL DATA", 20, 14, true);
    addText(`Average Temperature: ${weatherData.value.temp}°C`);
    addText(`Min/Max: ${weatherData.value.min}° / ${weatherData.value.max}°C`);
    addText(
      `Precipitation: ${weatherData.value.rain}mm (${weatherData.value.rainProb}%)`
    );
    yPosition += 5;

    if (historicalYearlyData.value.length > 0) {
      addText("Yearly Details:", 20, 12, true);
      historicalYearlyData.value.forEach((record) => {
        addText(
          `${record.date}: ${record.max}°/${record.min}°C, Rain: ${record.rainProb}%`,
          25
        );
      });
    }
  }

  doc.save("weather-report.pdf");
};

const downloadCSV = () => {
  let csvContent = "Type,Date,Temperature,Rain Probability,Min Temp,Max Temp\n";

  if (viewMode.value === "forecast" && forecastData.value) {
    csvContent += `Main Day,${forecastData.value.main_day.date},${forecastData.value.main_day.max}/${forecastData.value.main_day.min},${forecastData.value.main_day.rainProb},,\n`;
    forecastData.value.forecast.forEach((day) => {
      csvContent += `Forecast,${day.date},${day.max}/${day.min},${day.rainProb},,\n`;
    });
  } else if (viewMode.value === "historical" && weatherData.value) {
    csvContent += `Historical Average,,${weatherData.value.temp},${weatherData.value.rainProb},${weatherData.value.min},${weatherData.value.max}\n`;
    historicalYearlyData.value.forEach((record) => {
      csvContent += `Historical,${record.date},${record.max}/${record.min},${record.rainProb},,\n`;
    });
  }

  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "weather-data.csv";
  link.click();
  window.URL.revokeObjectURL(url);
};

const downloadJSON = () => {
  const data = {
    location:
      selectedCity.value ||
      (clickedCoordinates.value
        ? {
            lat: clickedCoordinates.value.lat,
            lng: clickedCoordinates.value.lng,
          }
        : null),
    date: `${selectedYear.value}-${Number(selectedMonth.value) + 1}-${
      selectedDay.value
    }`,
    viewMode: viewMode.value,
    forecastData: forecastData.value,
    historicalData: weatherData.value,
    historicalYearlyData: historicalYearlyData.value,
    recommendations: recommendations.value,
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "weather-data.json";
  link.click();
  window.URL.revokeObjectURL(url);
};

const downloadJPG = async () => {
  if (chartCanvas.value) {
    const image = chartCanvas.value.toDataURL("image/jpeg");
    const link = document.createElement("a");
    link.href = image;
    link.download = "weather-chart.jpg";
    link.click();
  } else {
    alert("No chart available for download");
  }
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
  z-index: 1001;
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
/* Estilos para el dropdown de descarga */
.dropdown {
  position: relative;
  display: inline-block;
}

.download-btn {
  background-color: #8b5cf6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s;
  height: 100%;
}

.download-btn:hover:not(:disabled) {
  background-color: #7c3aed;
}

.download-btn:disabled {
  background-color: #475569;
  cursor: not-allowed;
  opacity: 0.6;
}

.dropdown-content {
  display: none;
  position: absolute;
  background-color: #1e293b;
  min-width: 120px;
  box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
  z-index: 1002;
  border-radius: 6px;
  border: 1px solid #334155;
  right: 0;
}

.dropdown-content a {
  color: #e2e8f0;
  padding: 0.75rem 1rem;
  text-decoration: none;
  display: block;
  border-bottom: 1px solid #334155;
  transition: background-color 0.2s;
}

.dropdown-content a:last-child {
  border-bottom: none;
}

.dropdown-content a:hover {
  background-color: #334155;
}

.dropdown:hover .dropdown-content {
  display: block;
}
</style>
