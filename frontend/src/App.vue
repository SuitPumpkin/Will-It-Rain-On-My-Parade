<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <h1 class="app-title">
          <img :src="logoUrl" alt="Pronostika Logo" class="logo-image" />
          Pronostika
        </h1>
        <div class="header-controls">
          <button @click="startTour" class="tour-btn" title="Take a tour">
            <span class="tour-btn-icon">🚀</span>
            <span class="tour-btn-text">Guide</span>
          </button>
        </div>
      </div>
      <p class="app-subtitle">
        Search a location, see the essentials first, and explore the details
        when you need them.
      </p>
    </header>

    <WeatherMap ref="weatherMapComponent" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import WeatherMap from "./components/WeatherMap.vue";
import introJs from "intro.js";
import "intro.js/minified/introjs.min.css";
// eslint-disable-next-line no-unused-vars
import logoUrl from "@/assets/logo.png";

const weatherMapComponent = ref(null);

const tourSteps = [
  {
    element: ".topbar-brand",
    title: "🌍 Welcome to Pronostika",
    intro:
      "Your smart weather companion. Search any location worldwide and get instant forecasts or historical averages.",
    position: "right",
  },
  {
    element: ".search-container",
    title: "🔍 Search Cities",
    intro:
      "Type any city or country name. Suggestions appear as you type — press Enter or click to select.",
    position: "bottom",
  },
  {
    element: ".filters-toggle",
    title: "📅 Plan Your Date",
    intro:
      "Open the planning tools to pick a specific date, clear your pin, or check weather up to 2 years ahead.",
    position: "bottom",
  },
  {
    element: ".download-btn",
    title: "💾 Export Your Data",
    intro:
      "Download weather reports as PDF, CSV, JSON, or save the temperature chart as a JPG image.",
    position: "left",
  },
  {
    element: "#map",
    title: "🗺️ Interactive Map",
    intro:
      "Click anywhere on the map to drop a pin and get weather for those exact coordinates.",
    position: "top",
  },
  {
    element: ".dashboard-handle",
    title: "📊 Weather Dashboard",
    intro:
      "This expandable dock shows your weather summary, detailed forecasts, historical averages, and a 24-hour temperature chart. Click 'Details' to expand!",
    position: "top",
  },
  {
    element: ".view-toggle",
    title: "🔄 Forecast vs Historical",
    intro:
      "Toggle between future predictions (Forecast) and past 5-year averages (Historical) for any date.",
    position: "left",
  },
  {
    element: ".chart-container",
    title: "📈 24-Hour Temperature Chart",
    intro:
      "Visualize hourly temperature trends. The chart updates automatically when you switch views.",
    position: "top",
  },
];

const startTour = async () => {
  await nextTick(); // Wait for DOM update

  const intro = introJs();
  intro.setOptions({
    steps: tourSteps,
    showProgress: true,
    showBullets: true,
    exitOnOverlayClick: true,
    exitOnEsc: true,
    nextLabel: "Next →",
    prevLabel: "← Back",
    skipLabel: "Skip",
    doneLabel: "Finish",
    tooltipPosition: "auto",
    overlayOpacity: 0.75,
    positionPrecedence: ["bottom", "top", "left", "right"],
    scrollToElement: true,
    disableInteraction: false,
  });

  // Custom styling and animations
  intro.onbeforechange((targetElement) => {
    const tooltip = document.querySelector(".introjs-tooltip");
    if (tooltip) {
      tooltip.style.backgroundColor = "#0f172a";
      tooltip.style.border = "2px solid #22d3ee";
      tooltip.style.borderRadius = "12px";
      tooltip.style.boxShadow =
        "0 20px 50px rgba(2, 6, 23, 0.6), 0 0 0 1px rgba(34, 211, 228, 0.1)";
      tooltip.style.animation = "introjs-fade-in 0.3s ease-out";
    }

    const buttons = document.querySelectorAll(".introjs-button");
    buttons.forEach((button) => {
      button.style.background = "linear-gradient(135deg, #0ea5e9, #06b6d4)";
      button.style.color = "white";
      button.style.border = "none";
      button.style.borderRadius = "8px";
      button.style.padding = "10px 20px";
      button.style.fontWeight = "600";
      button.style.transition = "all 0.2s ease";
      button.style.boxShadow = "0 4px 14px rgba(14, 165, 233, 0.4)";
    });

    const skipButton = document.querySelector(".introjs-skipbutton");
    if (skipButton) {
      skipButton.style.background = "transparent";
      skipButton.style.color = "#94a3b8";
      skipButton.style.border = "1px solid #334155";
    }

    const prevButton = document.querySelector(".introjs-prevbutton");
    if (prevButton) {
      prevButton.style.background = "#334155";
      prevButton.style.boxShadow = "none";
    }

    // Highlight the target element
    if (targetElement) {
      targetElement.style.boxShadow =
        "0 0 0 4px rgba(34, 211, 228, 0.5), 0 8px 32px rgba(2, 6, 23, 0.4)";
      targetElement.style.transition = "box-shadow 0.3s ease";
    }
  });

  intro.oncomplete(() => {
    // Clean up highlights
    // eslint-disable-next-line prettier/prettier
    document.querySelectorAll('[style*="rgba(34, 211, 228"]').forEach((el) => {
      el.style.boxShadow = "";
      el.style.transition = "";
    });
  });

  intro.onexit(() => {
    // eslint-disable-next-line prettier/prettier
    document.querySelectorAll('[style*="rgba(34, 211, 228"]').forEach((el) => {
      el.style.boxShadow = "";
      el.style.transition = "";
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
    }, 1500);
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
  height: 100dvh;
  min-height: 100vh;
  background: #0f172a;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  overflow: hidden;
}

.app-header {
  position: absolute;
  inset: 0 0 auto;
  z-index: 1100;
  padding: 0.8rem clamp(1rem, 3vw, 2rem);
  background: linear-gradient(
    180deg,
    rgba(15, 23, 42, 0.92),
    rgba(15, 23, 42, 0)
  );
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
  display: none;
}

.header-badge {
  color: #bae6fd;
  background: rgba(14, 165, 233, 0.12);
  border: 1px solid rgba(14, 165, 233, 0.35);
  padding: 0.45rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
}

/* Tour Button */
.tour-btn {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.tour-btn:hover {
  background: linear-gradient(135deg, #7c3aed, #9333ea);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
}

.tour-btn:active {
  transform: translateY(0);
}

.tour-btn-icon {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

/* Custom Intro.js styling */
.introjs-tooltip {
  background: #0f172a !important;
  border: 2px solid #22d3ee !important;
  border-radius: 12px !important;
  color: #f1f5f9 !important;
  box-shadow: 0 20px 50px rgba(2, 6, 23, 0.6), 0 0 0 1px rgba(34, 211, 228, 0.1) !important;
  animation: introjs-fade-in 0.3s ease-out !important;
}

@keyframes introjs-fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.introjs-tooltip-title {
  color: #22d3ee !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid rgba(34, 211, 228, 0.2) !important;
  margin-bottom: 8px !important;
}

.introjs-tooltiptext {
  color: #cbd5e1 !important;
  line-height: 1.6 !important;
  font-size: 0.9rem !important;
}

.introjs-button {
  background: linear-gradient(135deg, #0ea5e9, #06b6d4) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 20px !important;
  font-weight: 600 !important;
  text-shadow: none !important;
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4) !important;
  transition: all 0.2s ease !important;
}

.introjs-button:hover {
  background: linear-gradient(135deg, #0284c7, #0891b2) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5) !important;
}

.introjs-button.introjs-disabled {
  background: #475569 !important;
  color: #94a3b8 !important;
  box-shadow: none !important;
  transform: none !important;
}

.introjs-skipbutton {
  background: transparent !important;
  color: #94a3b8 !important;
  border: 1px solid #334155 !important;
  border-radius: 8px !important;
}

.introjs-skipbutton:hover {
  background: #1e293b !important;
  color: #f1f5f9 !important;
}

.introjs-prevbutton {
  background: #334155 !important;
  box-shadow: none !important;
}

.introjs-prevbutton:hover {
  background: #475569 !important;
}

.introjs-bullets ul li a {
  background: #475569 !important;
  border-radius: 50% !important;
  width: 10px !important;
  height: 10px !important;
  transition: all 0.2s ease !important;
}

.introjs-bullets ul li a.active {
  background: #22d3ee !important;
  transform: scale(1.2) !important;
}

.introjs-progress {
  background: #1e293b !important;
  border-radius: 4px !important;
  height: 4px !important;
}

.introjs-progressbar {
  background: linear-gradient(90deg, #0ea5e9, #22d3ee) !important;
  border-radius: 4px !important;
  transition: width 0.3s ease !important;
}

.introjs-arrow {
  border-color: #0f172a !important;
}

.introjs-arrow.top {
  border-bottom-color: #0f172a !important;
}

.introjs-arrow.right {
  border-left-color: #0f172a !important;
}

.introjs-arrow.bottom {
  border-top-color: #0f172a !important;
}

.introjs-arrow.left {
  border-right-color: #0f172a !important;
}

.introjs-overlay {
  background: rgba(2, 6, 23, 0.75) !important;
  animation: overlay-fade-in 0.3s ease-out !important;
}

@keyframes overlay-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .app-header {
    padding: 0.75rem;
  }

  .header-content {
    gap: 0.5rem;
  }

  .header-controls {
    gap: 0.5rem;
  }

  .app-title {
    font-size: 1.5rem;
  }

  .app-subtitle {
    display: block;
    color: #94a3b8;
    font-size: 0.9rem;
    margin-top: 0.5rem;
  }

  .header-badge {
    display: none;
  }

  .tour-btn-text {
    display: none;
  }

  .tour-btn {
    padding: 10px;
  }
}

@media (max-width: 480px) {
  .tour-btn {
    padding: 8px;
  }
}
.logo-image {
  height: 2em;
  width: auto;
  vertical-align: middle;
  margin-right: 0.1rem;
}

/* Add to your existing responsive styles */
@media (max-width: 768px) {
  .logo-image {
    height: 1.1em;
    margin-right: 0.25rem;
  }
}
</style>
