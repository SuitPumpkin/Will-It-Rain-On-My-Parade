<script setup>
import { Line } from "vue-chartjs";
import { defineProps, reactive, watch } from "vue";

const props = defineProps({
  chartData: { type: Object, required: true },
  chartOptions: { type: Object, required: true },
});

const chartRef = reactive({});

watch(
  () => props.chartData,
  () => {
    if (chartRef.chart) {
      chartRef.chart.update();
    }
  }
);
</script>

<template>
  <Line ref="chartRef" :chart-data="chartData" :chart-options="chartOptions" />
</template>
