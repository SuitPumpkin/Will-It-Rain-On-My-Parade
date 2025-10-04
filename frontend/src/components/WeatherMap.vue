<template>
  <div class="weather-dashboard">
    <!-- Controles superiores -->
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

      <button @click="clearPin">Limpiar pin</button>

      <select v-model="selectedDay">
        <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
      </select>
      <select v-model="selectedMonth">
        <option v-for="(m, index) in months" :key="index" :value="index">
          {{ m }}
        </option>
      </select>

      <button @click="searchWeather">Obtener resultados</button>
    </div>

    <div class="main-content">
      <!-- Mapa a la izquierda -->
      <div id="map"></div>

      <!-- Panel derecho -->
      <div class="dashboard">
        <h2>Dashboard de Resultados</h2>

        <!-- Información de coordenadas del doble click -->
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
          <button @click="getWeatherForCoordinates" class="coords-button">
            Obtener clima para estas coordenadas
          </button>
        </div>

        <div class="stat" v-if="weatherData">
          <span>Temperatura (°C)</span>
          <span class="value">{{ weatherData.temp }}</span>
        </div>
        <div class="stat" v-if="weatherData">
          <span>Temperatura mínima / máxima</span>
          <span class="value"
            >{{ weatherData.min }} / {{ weatherData.max }}</span
          >
        </div>
        <div class="stat" v-if="weatherData">
          <span>Precipitación</span>
          <span class="value"
            >{{ weatherData.rain }} mm / {{ weatherData.rainProb }}%</span
          >
        </div>
        <div class="stat" v-if="weatherData">
          <span>Viento (km/h)</span>
          <span class="value">{{ weatherData.wind }}</span>
        </div>

        <div v-else-if="!clickedCoordinates" class="no-data">
          Selecciona una ubicación para ver los datos meteorológicos
        </div>

        <h3>Gráficos</h3>
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
// eslint-disable-next-line no-unused-vars
import { ref, onMounted, watch, computed, nextTick } from "vue";
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

// Estados reactivos
const searchCity = ref("");
const selectedCity = ref("");
const selectedDay = ref(new Date().getDate().toString());
const selectedMonth = ref(new Date().getMonth().toString());
const weatherData = ref(null);
const allCities = ref([]);
// eslint-disable-next-line no-unused-vars
const displayedCities = ref([]);
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

// Computed para fecha seleccionada
const selectedDate = computed(() => {
  const year = new Date().getFullYear();
  return `${year}-${String(Number(selectedMonth.value) + 1).padStart(
    2,
    "0"
  )}-${String(selectedDay.value).padStart(2, "0")}`;
});

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
    .slice(0, 15); // Limitar a 15 resultados
});

// Chart.js
const chartCanvas = ref(null);
let chartInstance = null;
let map = null;
let currentMarker = null;
let clickMarker = null; // Marcador para el doble click

// Funciones de autocompletado
const onSearchInput = () => {
  showSuggestionsList.value = searchCity.value.length >= 2;
  selectedSuggestionIndex.value = -1;
};

const showSuggestions = () => {
  if (searchCity.value.length >= 2) {
    showSuggestionsList.value = true;
  }
};

const hideSuggestions = () => {
  // Pequeño delay para permitir el click en las sugerencias
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

// Función para manejar doble click en el mapa
const setupMapDoubleClick = () => {
  if (!map) return;

  map.on("click", (e) => {
    const { lat, lng } = e.latlng;

    // Guardar coordenadas
    clickedCoordinates.value = {
      lat: lat,
      lng: lng,
    };

    // Limpiar marcador anterior de doble click
    if (clickMarker) {
      map.removeLayer(clickMarker);
    }

    // Crear nuevo marcador en la posición del doble click
    clickMarker = L.marker([lat, lng])
      .addTo(map)
      .bindPopup(
        `
        <div style="color: #000;">
          <b>Coordenadas seleccionadas</b><br>
          Lat: ${lat.toFixed(4)}<br>
          Lng: ${lng.toFixed(4)}<br>
          <em>Doble click para seleccionar</em>
        </div>
      `
      )
      .openPopup();

    // Centrar mapa en las coordenadas seleccionadas
    map.setView([lat, lng], map.getZoom());

    // Limpiar búsqueda de ciudad
    searchCity.value = "";
    selectedCity.value = "";
    weatherData.value = null;
  });
};

// Obtener clima para las coordenadas seleccionadas
const getWeatherForCoordinates = () => {
  if (!clickedCoordinates.value) return;

  const { lat, lng } = clickedCoordinates.value;

  // Limpiar marcador anterior si existe
  if (currentMarker) {
    map.removeLayer(currentMarker);
  }

  // Obtener datos meteorológicos
  const fakeData = getFakeWeather(lat, lng, selectedDate.value);
  weatherData.value = fakeData;

  // Crear marcador para el clima
  currentMarker = L.marker([lat, lng])
    .addTo(map)
    .bindPopup(
      `
      <div style="color: #000;">
        <b>Coordenadas personalizadas</b><br>
        Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}<br>
        Temperatura: ${fakeData.temp}°C<br>
        Mín/Máx: ${fakeData.min}°C / ${fakeData.max}°C<br>
        Viento: ${fakeData.wind} km/h<br>
        ${fakeData.description}
      </div>
    `
    )
    .openPopup();
};

// Navegación con teclado
const handleKeydown = (event) => {
  if (!showSuggestionsList.value) return;

  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      selectedSuggestionIndex.value =
        selectedSuggestionIndex.value < filteredCities.value.length - 1
          ? selectedSuggestionIndex.value + 1
          : 0;
      break;
    case "ArrowUp":
      event.preventDefault();
      selectedSuggestionIndex.value =
        selectedSuggestionIndex.value > 0
          ? selectedSuggestionIndex.value - 1
          : filteredCities.value.length - 1;
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

// Agregar event listener para teclado
onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
});

const createChart = () => {
  if (chartCanvas.value && ChartJS.registry.getController("line")) {
    const ctx = chartCanvas.value.getContext("2d");

    if (chartInstance) {
      chartInstance.destroy();
    }

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
            pointBackgroundColor: "#4a90e2",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 2,
            pointRadius: 4,
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
            labels: {
              color: "#f1f5f9",
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(30, 41, 59, 0.9)",
            titleColor: "#f1f5f9",
            bodyColor: "#f1f5f9",
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            grid: {
              color: "rgba(255,255,255,0.1)",
            },
            ticks: {
              color: "#f1f5f9",
              callback: function (value) {
                return value + "°C";
              },
            },
          },
          x: {
            grid: {
              color: "rgba(255,255,255,0.1)",
            },
            ticks: {
              color: "#f1f5f9",
              maxRotation: 45,
            },
          },
        },
      },
    });
  }
};

// Actualizar gráfico
watch(
  hourlyData,
  (newData) => {
    if (chartInstance && newData) {
      chartInstance.data.labels = newData.map((d) => d.hour);
      chartInstance.data.datasets[0].data = newData.map((d) => d.temp);
      chartInstance.update("active");
    }
  },
  { deep: true }
);

// Limpiar marcador del mapa
function clearPin() {
  if (currentMarker) {
    map.removeLayer(currentMarker);
    currentMarker = null;
  }
  if (clickMarker) {
    map.removeLayer(clickMarker);
    clickMarker = null;
  }
  weatherData.value = null;
  searchCity.value = "";
  selectedCity.value = "";
  showSuggestionsList.value = false;
  clickedCoordinates.value = null;

  // Resetear datos del gráfico
  hourlyData.value = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: 0,
  }));
}

// Generar datos meteorológicos simulados mejorados
// eslint-disable-next-line no-unused-vars
function getFakeWeather(lat, lon, date) {
  const baseTemp = 20 + lat / 10 + Math.sin(lon) * 5;
  const hourTemps = Array.from({ length: 24 }, (_, i) => {
    const hourVariation = Math.sin(((i - 6) * Math.PI) / 12) * 8;
    return (
      Math.round((baseTemp + hourVariation + (Math.random() * 4 - 2)) * 10) / 10
    );
  });

  hourlyData.value = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: hourTemps[i],
  }));

  return {
    temp: Math.round(baseTemp),
    min: Math.min(...hourTemps).toFixed(1),
    max: Math.max(...hourTemps).toFixed(1),
    rain: (Math.random() * 20).toFixed(1),
    rainProb: Math.floor(Math.random() * 100),
    wind: Math.floor(Math.random() * 50),
    feels_like: Math.round(baseTemp + 2),
    humidity: Math.floor(Math.random() * 40) + 40,
    description: "Soleado con nubes",
  };
}

// Buscar clima con ciudad específica
function searchWeatherWithCity(city) {
  selectedCity.value = city.city;
  const coords = [city.lat, city.lng];

  map.setView(coords, 10);
  clearPin();

  const fakeData = getFakeWeather(coords[0], coords[1], selectedDate.value);
  weatherData.value = fakeData;

  currentMarker = L.marker(coords)
    .addTo(map)
    .bindPopup(
      `
      <div style="color: #000;">
        <b>${selectedCity.value}</b><br>
        Lat: ${coords[0].toFixed(4)}, Lng: ${coords[1].toFixed(4)}<br>
        Temperatura: ${fakeData.temp}°C<br>
        Mín/Máx: ${fakeData.min}°C / ${fakeData.max}°C<br>
        Viento: ${fakeData.wind} km/h<br>
        ${fakeData.description}
      </div>
    `
    )
    .openPopup();
}

// Buscar clima
function searchWeather() {
  if (!searchCity.value.trim()) {
    alert("Por favor, ingresa una ciudad para buscar");
    return;
  }

  // Si hay una ciudad seleccionada de las sugerencias, usarla
  if (selectedCity.value) {
    const city = allCities.value.find((c) => c.city === selectedCity.value);
    if (city) {
      searchWeatherWithCity(city);
      return;
    }
  }

  // Si no, buscar por texto
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

// Inicializar aplicación
onMounted(async () => {
  // Inicializar mapa
  map = L.map("map").setView([23.6345, -102.5528], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  // Configurar evento de doble click
  setupMapDoubleClick();

  // Cargar ciudades
  try {
    const res = await fetch("/datasets/worldcities.json");
    const data = await res.json();
    allCities.value = data.map((c) => ({
      city: c.city,
      lat: parseFloat(c.lat),
      lng: parseFloat(c.lng),
      country: c.country,
    }));
  } catch (err) {
    console.error("Error al cargar ciudades:", err);
    // Datos de fallback para desarrollo
    allCities.value = [
      {
        city: "Ciudad de México",
        lat: 19.4326,
        lng: -99.1332,
        country: "Mexico",
      },
      { city: "Madrid", lat: 40.4168, lng: -3.7038, country: "Spain" },
      {
        city: "Buenos Aires",
        lat: -34.6037,
        lng: -58.3816,
        country: "Argentina",
      },
      { city: "Lima", lat: -12.0464, lng: -77.0428, country: "Peru" },
      { city: "Bogotá", lat: 4.711, lng: -74.0721, country: "Colombia" },
      { city: "Santiago", lat: -33.4489, lng: -70.6693, country: "Chile" },
      {
        city: "New York",
        lat: 40.7128,
        lng: -74.006,
        country: "United States",
      },
      { city: "London", lat: 51.5074, lng: -0.1278, country: "United Kingdom" },
      { city: "Tokyo", lat: 35.6762, lng: 139.6503, country: "Japan" },
    ];
  }

  setTimeout(() => {
    createChart();
  }, 100);
});

// Limpiar al desmontar el componente
import { onUnmounted } from "vue";
onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
  if (chartInstance) {
    chartInstance.destroy();
  }
  if (map) {
    map.remove();
  }
});
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
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  align-items: center;
  position: relative;
}

.search-container {
  position: relative;
  flex: 1;
  min-width: 300px;
}

.controls input,
.controls select,
.controls button {
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  border: none;
  font-size: 0.95rem;
}

.controls input {
  width: 100%;
  background: #1e293b;
  color: white;
}

.controls select {
  background: #1e293b;
  color: white;
}

.controls button {
  background-color: #0ea5e9;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.controls button:hover {
  background-color: #0284c7;
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
}

.country-name {
  color: #94a3b8;
  font-size: 0.875rem;
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

.main-content {
  display: flex;
  gap: 1rem;
  flex: 1;
}

#map {
  flex: 2;
  height: 500px;
  border-radius: 12px;
  border: 1px solid #334155;
  cursor: pointer;
}

.dashboard {
  flex: 1;
  background: #1e293b;
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 500px;
}

.dashboard h2,
.dashboard h3 {
  margin: 0;
  color: #f1f5f9;
}

.stat {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #334155;
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

canvas {
  background: #0f172a;
  border-radius: 8px;
  height: 200px !important;
  width: 100% !important;
}

/* Responsive */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }

  #map {
    height: 300px;
  }

  .search-container {
    min-width: 100%;
  }

  .controls {
    gap: 0.5rem;
  }
}
</style>
