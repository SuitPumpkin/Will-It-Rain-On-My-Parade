<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">🌤️ Pronostika</h1>
        <div class="header-controls">
          <div class="mode-switcher">
            <span class="mode-label">{{
              isComplexMode ? "Deep Dive" : "Quick look"
            }}</span>
            <label class="switch">
              <input type="checkbox" v-model="isComplexMode" />
              <span class="slider"></span>
            </label>
          </div>
          <button @click="startTour" class="tour-btn" title="Take a tour">
            🚀 Guide
          </button>
        </div>
      </div>
      <p class="app-subtitle">
        {{
          isComplexMode
            ? "Advanced Weather Analytics & Forecasting"
            : "Simple weather checking for everyone!"
        }}
      </p>
    </header>

    <WeatherMap v-if="isComplexMode" ref="weatherMapComponent" />
    <WeatherMapSimple v-else ref="weatherMapSimpleComponent" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import WeatherMap from "./components/WeatherMap.vue";
import WeatherMapSimple from "./components/WeatherMapSimple.vue";
import introJs from "intro.js";
import "intro.js/minified/introjs.min.css";

const isComplexMode = ref(true);
const weatherMapComponent = ref(null);
const weatherMapSimpleComponent = ref(null);

// Tour steps for both modes
const expertTourSteps = [
  {
    element: ".search-container",
    title: "🔍 Search Cities",
    intro: "Search for any city worldwide to get weather information.",
    position: "bottom",
  },
  {
    element: ".controls-group",
    title: "📅 Date Selection",
    intro:
      "Select the year, month, and day for historical weather data analysis.",
    position: "bottom",
  },
  {
    element: ".download-btn",
    title: "💾 Download Data",
    intro: "Export weather data in multiple formats: PDF, CSV, JSON, or JPG.",
    position: "left",
  },
  {
    element: "#map",
    title: "🗺️ Interactive Map",
    intro:
      "Click anywhere on the map to get weather data for specific coordinates.",
    position: "top",
  },
  {
    element: ".view-toggle",
    title: "📊 Data Views",
    intro:
      "Switch between Forecast (future predictions) and Historical (past data) views.",
    position: "left",
  },
  {
    element: ".chart-container",
    title: "📈 Temperature Chart",
    intro: "Visualize 24-hour temperature trends with this interactive chart.",
    position: "top",
  },
  {
    element: ".mode-switcher",
    title: "🎛️ Mode Switch",
    intro:
      "Toggle between Expert Mode (advanced features) and Simple Mode (easy-to-use interface).",
    position: "left",
  },
];

const simpleTourSteps = [
  {
    element: ".simple-search",
    title: "🔍 Easy Search",
    intro: "Type a city name to find weather information quickly.",
    position: "bottom",
  },
  {
    element: ".date-selector",
    title: "📅 Select Date",
    intro: "Choose when you want to check the weather.",
    position: "bottom",
  },
  {
    element: "#simple-map",
    title: "🗺️ Click the Map",
    intro: "Click anywhere on the map to check weather for that location!",
    position: "top",
  },
  {
    element: ".search-btn",
    title: "🌤️ Get Weather",
    intro: "Click here to check if you need an umbrella!",
    position: "left",
  },
  {
    element: ".result-card",
    title: "📋 Weather Results",
    intro:
      "See clear weather information with easy-to-understand recommendations.",
    position: "top",
  },
  {
    element: ".forecast-simple",
    title: "📅 Next Days",
    intro: "Check the weather forecast for the next few days.",
    position: "top",
  },
  {
    element: ".mode-switcher",
    title: "🔄 Switch Modes",
    intro: "Try Expert Mode for more detailed weather analysis!",
    position: "left",
  },
];

const startTour = async () => {
  await nextTick(); // Wait for DOM update

  const steps = isComplexMode.value ? expertTourSteps : simpleTourSteps;

  const intro = introJs();
  intro.setOptions({
    steps: steps,
    showProgress: true,
    showBullets: true,
    exitOnOverlayClick: true,
    exitOnEsc: true,
    nextLabel: "Next →",
    prevLabel: "← Back",
    skipLabel: "Skip",
    doneLabel: "Finish",
    tooltipPosition: "auto",
    overlayOpacity: 0.7,
    positionPrecedence: ["bottom", "top", "left", "right"],
  });

  // Add custom styling
  intro.onbeforechange(() => {
    const tooltip = document.querySelector(".introjs-tooltip");
    if (tooltip) {
      tooltip.style.backgroundColor = "#1e293b";
      tooltip.style.border = "2px solid #334155";
      tooltip.style.borderRadius = "8px";
    }

    const buttons = document.querySelectorAll(".introjs-button");
    buttons.forEach((button) => {
      button.style.background = "#0ea5e9";
      button.style.color = "white";
      button.style.border = "none";
      button.style.borderRadius = "4px";
    });
  });

  intro.start();
};

// Auto-start tour on first visit
onMounted(() => {
  const hasTakenTour = localStorage.getItem("pronostika_tour_taken");
  if (!hasTakenTour) {
    setTimeout(() => {
      startTour();
      localStorage.setItem("pronostika_tour_taken", "true");
    }, 1000);
  }
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app {
  min-height: 100vh;
  background: #0f172a;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.app-header {
  background: #1e293b;
  padding: 1rem;
  border-bottom: 1px solid #334155;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.app-title {
  color: #f1f5f9;
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

.app-subtitle {
  color: #94a3b8;
  text-align: center;
  margin-top: 0.5rem;
  font-size: 1rem;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
}

/* Mode Switcher Styles */
.mode-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(30, 41, 59, 0.8);
  padding: 8px 16px;
  border-radius: 25px;
  border: 1px solid #475569;
}

.mode-label {
  color: #e2e8f0;
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
}

/* Tour Button */
.tour-btn {
  background: #8b5cf6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 25px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #8b5cf6;
  white-space: nowrap;
}

.tour-btn:hover {
  background: #7c3aed;
  transform: translateY(-1px);
}

/* Switch styles */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #475569;
  transition: 0.3s;
  border-radius: 22px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #0ea5e9;
}

input:checked + .slider:before {
  transform: translateX(22px);
}

/* Custom Intro.js styling */
.introjs-tooltip {
  background: #1e293b !important;
  border: 2px solid #334155 !important;
  border-radius: 8px !important;
  color: #f1f5f9 !important;
}

.introjs-tooltip-title {
  color: #0ea5e9 !important;
  font-weight: 600 !important;
}

.introjs-tooltiptext {
  color: #cbd5e1 !important;
}

.introjs-button {
  background: #0ea5e9 !important;
  color: white !important;
  border: none !important;
  border-radius: 4px !important;
  text-shadow: none !important;
}

.introjs-button:hover {
  background: #0284c7 !important;
}

.introjs-button.introjs-disabled {
  background: #475569 !important;
  color: #94a3b8 !important;
}

.introjs-bullets ul li a {
  background: #475569 !important;
}

.introjs-bullets ul li a.active {
  background: #0ea5e9 !important;
}

.introjs-progress {
  background: #334155 !important;
}

.introjs-progressbar {
  background: #0ea5e9 !important;
}

.introjs-arrow {
  border-color: #1e293b !important;
}

.introjs-arrow.top {
  border-bottom-color: #1e293b !important;
}

.introjs-arrow.right {
  border-left-color: #1e293b !important;
}

.introjs-arrow.bottom {
  border-top-color: #1e293b !important;
}

.introjs-arrow.left {
  border-right-color: #1e293b !important;
}

/* Responsive */
@media (max-width: 768px) {
  .app-header {
    padding: 0.75rem;
  }

  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .header-controls {
    flex-direction: column;
    gap: 10px;
  }

  .app-title {
    font-size: 1.5rem;
  }

  .app-subtitle {
    font-size: 0.9rem;
    margin-top: 0.25rem;
  }
}

@media (max-width: 480px) {
  .mode-switcher {
    padding: 6px 12px;
  }

  .mode-label {
    font-size: 0.8rem;
  }

  .switch {
    width: 40px;
    height: 20px;
  }

  .slider:before {
    height: 14px;
    width: 14px;
  }

  .tour-btn {
    padding: 6px 12px;
    font-size: 0.8rem;
  }
}
</style>
