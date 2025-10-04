<template>
  <div id="app">
    <h1 class="title">Tamales.exe || ¿Va a llover?</h1>

    <!-- Formulario -->
    <div class="form">
      <label>
        Selecciona una ciudad:
        <select v-model="selectedCity">
          <option disabled value="">-- Elige una ciudad --</option>
          <option
            v-for="(coords, city) in cities"
            :key="city"
            :value="city"
          >
            {{ city }}
          </option>
        </select>
      </label>

      <label>
        Selecciona una fecha:
        <div class="date-controls">
          <button @click="cambiarDia(-1)">⬅️</button>
          <input type="date" v-model="selectedDate" />
          <button @click="cambiarDia(1)">➡️</button>
        </div>
      </label>

      <button @click="buscarCiudad">Buscar</button>
    </div>

    <!-- Contenedor principal -->
    <div class="main-container">
      <div id="map"></div>

      <div class="weather-panel" v-if="weather">
        <h2>Clima en {{ selectedCity }}</h2>
        <p><b>Temperatura:</b> {{ weather.temp }}°C</p>
        <p><b>Sensación térmica:</b> {{ weather.feels_like }}°C</p>
        <p><b>Humedad:</b> {{ weather.humidity }}%</p>
        <p><b>Condición:</b> {{ weather.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const map = ref(null);
const marker = ref(null);
const selectedCity = ref("");
const selectedDate = ref("");
const weather = ref(null);

const cities = {
  "Ciudad de México": [19.4326, -99.1332],
  Guadalajara: [20.6597, -103.3496],
  Monterrey: [25.6866, -100.3161],
  Cancún: [21.1619, -86.8515],
};

onMounted(() => {
  map.value = L.map("map").setView([23.6345, -102.5528], 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
  }).addTo(map.value);
});

async function buscarCiudad() {
  if (!selectedCity.value || !selectedDate.value) {
    alert("Por favor selecciona ciudad y fecha.");
    return;
  }

  const coords = cities[selectedCity.value];
  map.value.setView(coords, 13, { animate: true });

  if (marker.value) map.value.removeLayer(marker.value);
  marker.value = L.marker(coords).addTo(map.value);
  marker.value
    .bindPopup(`<b>${selectedCity.value}</b><br>Fecha: ${selectedDate.value}`)
    .openPopup();

  await fetchWeatherFromBackend(coords[0], coords[1], selectedDate.value);
}

async function cambiarDia(direccion) {
  if (!selectedCity.value) {
    alert("Por favor selecciona primero una ciudad.");
    return;
  }

  if (!selectedDate.value) {
    selectedDate.value = new Date().toISOString().split("T")[0];
  } else {
    const fecha = new Date(selectedDate.value);
    fecha.setDate(fecha.getDate() + direccion);
    selectedDate.value = fecha.toISOString().split("T")[0];
  }

  if (marker.value) {
    marker.value
      .setPopupContent(`<b>${selectedCity.value}</b><br>Fecha: ${selectedDate.value}`)
      .openPopup();
  }

  const coords = cities[selectedCity.value];
  await fetchWeatherFromBackend(coords[0], coords[1], selectedDate.value);
}

// 🔧 versión real: consulta el backend Flask
async function fetchWeatherFromBackend(lat, lon, date) {
  try {
    const res = await fetch(`http://localhost:5000/api/weather?lat=${lat}&lon=${lon}&date=${date}`);
    const data = await res.json();

    weather.value = {
      temp: data.temp,
      feels_like: data.feels_like,
      humidity: data.humidity,
      description: data.description,
    };
  } catch (err) {
    console.error("Error al obtener el clima del backend:", err);
    weather.value = null;
  }
}

// 💡 si aún no tienes backend funcionando, puedes usar estos datos de prueba:
const mockWeatherData = {
  "Ciudad de México": { temp: 25, feels_like: 27, humidity: 60, description: "Soleado con nubes" },
  Guadalajara: { temp: 28, feels_like: 30, humidity: 55, description: "Parcialmente nublado" },
  Monterrey: { temp: 32, feels_like: 35, humidity: 40, description: "Soleado" },
  Cancún: { temp: 30, feels_like: 33, humidity: 70, description: "Lluvia ligera" },
};

// si quieres usar mock temporalmente, comenta la función real y usa esta:
///*
// async function fetchWeatherFromBackend(lat, lon, date) {
//   const city = Object.keys(cities).find(
//     c => cities[c][0] === lat && cities[c][1] === lon
//   );
//   if (city) {
//     setTimeout(() => {
//       weather.value = mockWeatherData[city];
//     }, 300);
//   } else {
//     weather.value = null;
//   }
// }
//*/
</script>

<style scoped>
body {
  margin: 0;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  background: #f2f6ff;
  color: #333;
}
#app {
  max-width: 900px;
  margin: 2rem auto;
  padding: 1rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}
.title {
  text-align: center;
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 1.5rem;
}
.form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
  align-items: center;
  margin-bottom: 1.5rem;
}
.form label {
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
  box-shadow: 0 0 5px rgba(74, 144, 226, 0.5);
}
button {
  padding: 0.5rem 1rem;
  background: #4a90e2;
  color: white;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
button:hover {
  background: #357abd;
}
.date-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.date-controls button {
  background: #7fb3ff;
  padding: 0.4rem 0.8rem;
}
.date-controls button:hover {
  background: #5a94e5;
}
#map {
  height: 500px;
  width: 100%;
  border-radius: 12px;
  border: 1px solid #d0d7e0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}
#map:hover {
  transform: scale(1.01);
}
.main-container {
  display: flex;
  gap: 1rem;
}
.weather-panel {
  width: 250px;
  padding: 1rem;
  background: #f0f4ff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}
.weather-panel h2 {
  margin-top: 0;
  font-size: 1.2rem;
  color: #2c3e50;
}
.weather-panel p {
  margin: 0.3rem 0;
}
</style>
