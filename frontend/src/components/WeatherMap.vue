<template>
  <div class="weather-app">
    <h1 class="title">Tamales.exe || ¿Va a llover?</h1>

    <!-- Controles -->
    <div class="controls">
      <label>
        Ciudad:
        <select v-model="selectedCity">
          <option disabled value="">-- Selecciona una ciudad --</option>
          <option v-for="c in displayedCities" :key="c.city" :value="c.city">
            {{ c.city }}
          </option>
          <option
            v-if="displayedCities.length < allCities.length"
            @click="loadMoreCities"
            disabled
          >
            Cargar más...
          </option>
        </select>
      </label>

      <label>
        Fecha:
        <div class="date-controls">
          <button @click="changeDay(-1)">⬅️</button>
          <input type="date" v-model="selectedDate" />
          <button @click="changeDay(1)">➡️</button>
        </div>
      </label>

      <button class="btn-search" @click="searchWeather">Buscar</button>
    </div>

    <!-- Contenedor principal: mapa + panel de clima -->
    <div class="main-container">
      <div id="map"></div>

      <div v-if="weatherData" class="weather-panel">
        <h2>Clima en {{ selectedCity }}</h2>
        <p><b>Temperatura:</b> {{ weatherData.temp }}°C</p>
        <p><b>Sensación térmica:</b> {{ weatherData.feels_like }}°C</p>
        <p><b>Humedad:</b> {{ weatherData.humidity }}%</p>
        <p><b>Condición:</b> {{ weatherData.description }}</p>

        <!-- Gráfico de temperatura por hora -->
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
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
} from "chart.js";

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement
);

// Estados
const selectedCity = ref("");
const selectedDate = ref(new Date().toISOString().slice(0, 10));
const weatherData = ref(null);
const allCities = ref([]);
const displayedCities = ref([]);
const hourlyData = ref(
  Array.from({ length: 24 }, (_, i) => ({ hour: `${i}:00`, temp: 0 }))
);
const CHUNK_SIZE = 50;

// Chart.js
const chartCanvas = ref(null);
let chartInstance = null;

const createChart = () => {
  if (chartCanvas.value) {
    chartInstance = new ChartJS(chartCanvas.value, {
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
        plugins: { legend: { display: true, position: "top" } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }
};

// Actualizar gráfico al cambiar los datos
watch(
  hourlyData,
  (newData) => {
    if (chartInstance) {
      chartInstance.data.labels = newData.map((d) => d.hour);
      chartInstance.data.datasets[0].data = newData.map((d) => d.temp);
      chartInstance.update();
    }
  },
  { deep: true }
);

// Cargar más ciudades
function loadMoreCities() {
  const current = displayedCities.value.length;
  displayedCities.value.push(
    ...allCities.value.slice(current, current + CHUNK_SIZE)
  );
}

// eslint-disable-next-line no-unused-vars
function getFakeWeather(lat, lon, date) {
  // lat, lon, date para futura compatibilidad
  hourlyData.value = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: Math.floor(Math.random() * 15) + 15,
  }));

  const random = Math.floor(Math.random() * 5);
  return [
    {
      temp: 25,
      feels_like: 27,
      humidity: 60,
      description: "Soleado con nubes",
    },
    {
      temp: 28,
      feels_like: 30,
      humidity: 55,
      description: "Parcialmente nublado",
    },
    { temp: 30, feels_like: 33, humidity: 70, description: "Lluvia ligera" },
    { temp: 22, feels_like: 22, humidity: 80, description: "Lluvia moderada" },
    {
      temp: 18,
      feels_like: 17,
      humidity: 90,
      description: "Tormenta eléctrica",
    },
  ][random];
}

// Buscar clima
function searchWeather() {
  if (!selectedCity.value) return;

  const city = allCities.value.find((c) => c.city === selectedCity.value);
  if (!city) return;

  const coords = [city.lat, city.lng];
  map.setView(coords, 10);

  const fakeData = getFakeWeather(coords[0], coords[1], selectedDate.value);
  weatherData.value = fakeData;

  L.marker(coords)
    .addTo(map)
    .bindPopup(
      `
      <b>${selectedCity.value}</b><br>
      Fecha: ${selectedDate.value}<br>
      Temperatura: ${fakeData.temp}°C<br>
      Sensación: ${fakeData.feels_like}°C<br>
      Humedad: ${fakeData.humidity}%<br>
      ${fakeData.description}
    `
    )
    .openPopup();
}

// Cambiar día
function changeDay(days) {
  const date = new Date(selectedDate.value);
  date.setDate(date.getDate() + days);
  selectedDate.value = date.toISOString().slice(0, 10);
}

// Inicializar mapa y cargar ciudades
let map;
onMounted(async () => {
  // Inicializar mapa
  map = L.map("map").setView([23.6345, -102.5528], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  // Cargar ciudades desde public
  try {
    const res = await fetch("/datasets/worldcities.json");
    const data = await res.json();
    allCities.value = data.map((c) => ({
      city: c.city,
      lat: parseFloat(c.lat),
      lng: parseFloat(c.lng),
    }));
    displayedCities.value = allCities.value.slice(0, CHUNK_SIZE);
  } catch (err) {
    console.error("Error al cargar ciudades:", err);
  }

  createChart();
});
</script>

<style scoped>
.weather-app {
  max-width: 1000px;
  margin: 2rem auto;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: #f9fbff;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}
.title {
  text-align: center;
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 1.5rem;
}
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
  align-items: center;
  margin-bottom: 1.5rem;
}
label {
  display: flex;
  flex-direction: column;
  font-weight: 500;
  color: #34495e;
}
select,
input[type="date"] {
  padding: 0.5rem 0.75rem;
  margin-top: 0.3rem;
  border: 1px solid #ccd6f6;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
}
select:focus,
input[type="date"]:focus {
  border-color: #4a90e2;
  outline: none;
  box-shadow: 0 0 8px rgba(74, 144, 226, 0.4);
}
.date-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
button {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
button:hover {
  transform: translateY(-2px);
}
.btn-search {
  background: linear-gradient(90deg, #4a90e2, #357abd);
  color: white;
}
.btn-search:hover {
  background: linear-gradient(90deg, #357abd, #2c3e50);
}
.main-container {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
#map {
  flex: 2;
  height: 500px;
  border-radius: 12px;
  border: 1px solid #d0d7e0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}
#map:hover {
  transform: scale(1.01);
}
.weather-panel {
  flex: 1;
  padding: 1rem 1.2rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  height: fit-content;
}
.weather-panel h2 {
  margin-top: 0;
  font-size: 1.3rem;
  color: #2c3e50;
}
.weather-panel p {
  margin: 0.4rem 0;
}
@media (max-width: 900px) {
  .main-container {
    flex-direction: column;
  }
  #map {
    width: 100%;
  }
  .weather-panel {
    width: 100%;
  }
}
</style>
