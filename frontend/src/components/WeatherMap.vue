<template>
  <div class="weather-app">
    <h1 class="title">Tamales.exe || ¿Va a llover?</h1>

    <div class="controls">
      <label>
        Ciudad:
        <select v-model="selectedCity">
          <option disabled value="">-- Selecciona una ciudad --</option>
          <option
            v-for="city in Object.keys(cities).sort()"
            :key="city"
            :value="city"
          >
            {{ city }}
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

      <button class="btn-search" @click="searchWeather" :disabled="isLoading">
        {{ isLoading ? "Buscando..." : "Buscar" }}
      </button>
    </div>

    <div v-if="error" class="error-panel">⚠️ Error: {{ error }}</div>

    <div class="main-container">
      <div id="map"></div>

      <div v-if="isLoading" class="weather-panel loading-panel">
        <p>Obteniendo datos del clima...</p>
        <div class="spinner"></div>
      </div>

      <div v-else-if="weatherData" class="weather-panel">
        <h2>Clima en {{ weatherData.ciudad }}</h2>
        <p><b>Temperatura:</b> {{ weatherData.temperatura }}°C</p>
        <p><b>Sensación térmica:</b> {{ weatherData.sensacion_real }}°C</p>
        <p><b>Humedad:</b> {{ weatherData.humedad }}%</p>
        <p><b>Condición:</b> {{ weatherData.descripcion }}</p>
      </div>

      <div v-else-if="!error" class="weather-panel">
        <h2>Bienvenido</h2>
        <p>
          Selecciona una ciudad y haz clic en "Buscar" para ver el pronóstico
          del tiempo.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css"; // Es buena práctica importar los CSS de leaflet

// Importamos las ciudades desde JSON
import citiesData from "@/datasets/worldcities.json";

// --- ESTADO DEL COMPONENTE ---
const selectedCity = ref("Guadalajara"); // Valor inicial para una mejor demo
const selectedDate = ref(new Date().toISOString().slice(0, 10));

// Los datos del clima, el estado de carga y el manejo de errores
const weatherData = ref(null);
const isLoading = ref(false);
const error = ref(null);

// --- PROCESAMIENTO INICIAL DE DATOS ---
const cities = {};
citiesData.forEach((city) => {
  const lat = parseFloat(city.lat);
  const lng = parseFloat(city.lng);
  if (!isNaN(lat) && !isNaN(lng)) {
    // Usamos el nombre de la ciudad como clave para un acceso fácil
    cities[city.city] = [lat, lng];
  }
});

// Referencia al mapa de Leaflet
let map;
let marker; // Guardamos una referencia al marcador para poder moverlo

// --- CICLO DE VIDA ---
onMounted(() => {
  // Inicializamos el mapa centrado en México
  map = L.map("map").setView([23.6345, -102.5528], 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Hacemos una búsqueda inicial al cargar la página
  searchWeather();
});

// --- MÉTODOS ---

// La función principal que se conecta a nuestro backend
async function searchWeather() {
  // Guarda la ciudad seleccionada para evitar cambios durante la ejecución
  const cityToSearch = selectedCity.value;

  if (!cityToSearch) {
    error.value = "Por favor, selecciona una ciudad.";
    return;
  }

  // 1. Reiniciar estados antes de cada búsqueda
  isLoading.value = true;
  error.value = null;
  weatherData.value = null;

  try {
    // 2. Obtener las coordenadas de la ciudad seleccionada
    const coords = cities[cityToSearch];
    if (!coords) {
      throw new Error(`Coordenadas no encontradas para: ${cityToSearch}`);
    }

    // 3. Construir la URL y llamar a nuestro backend con latitud y longitud
    const apiUrl = `http://127.0.0.1:5000/clima?lat=${coords[0]}&lon=${coords[1]}`;
    const response = await fetch(apiUrl);

    // Si la respuesta del backend no es exitosa, lanzar un error
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Ocurrió un error desconocido.");
    }

    // 4. Si todo salió bien, procesar los datos
    const data = await response.json();
    weatherData.value = data;

    // 5. Actualizar la vista del mapa y el marcador
    map.setView(coords, 10);

    if (marker) {
      marker.setLatLng(coords);
    } else {
      marker = L.marker(coords).addTo(map);
    }
    
    marker.bindPopup(`
        <b>${data.ciudad}</b><br>
        ${data.descripcion}<br>
        Temperatura: ${data.temperatura}°C
      `).openPopup();

  } catch (err) {
    // 6. Si ocurre cualquier error, lo capturamos y mostramos
    console.error("Error al buscar el clima:", err);
    error.value = err.message;
  } finally {
    // 7. Al final de todo (éxito o error), se desactiva el estado de carga
    isLoading.value = false;
  }
}

// Función para cambiar el día (sin cambios, ya funcionaba bien)
function changeDay(days) {
  const date = new Date(selectedDate.value);
  // Aseguramos que la fecha se interprete en UTC para evitar problemas de zona horaria
  date.setUTCDate(date.getUTCDate() + days);
  selectedDate.value = date.toISOString().slice(0, 10);
}
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

/* Contenedor principal */
.main-container {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

/* Mapa */
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

/* Panel de clima */
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

/* Responsive: panel debajo del mapa en pantallas pequeñas */
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
/* ... tus estilos existentes ... */

.error-panel {
  background-color: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.loading-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  color: #34495e;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #4a90e2;
  animation: spin 1s ease infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
  transform: none;
}
</style>
