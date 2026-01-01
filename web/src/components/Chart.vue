<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import * as d3 from "d3";
import { plot } from "simple-ascii-chart";

const props = withDefaults(
  defineProps<{
    data: number[];
    lib?: "d3" | "ascii";
    height?: number;
    width?: number; // For D3 SVG viewBox
    color?: string;
  }>(),
  {
    lib: "d3",
    height: 40,
    width: 100,
    color: "#6366f1", // Indigo-500
  }
);

// D3 Path Computation
const d3Path = computed(() => {
  if (props.lib !== "d3" || !props.data.length) return "";

  const data = props.data.length > 1 ? props.data : [0, ...props.data]; // Ensure at least 2 points for line

  const xScale = d3
    .scaleLinear()
    .domain([0, data.length - 1])
    .range([0, props.width]);

  const maxVal = Math.max(...data, 0.1);
  const yScale = d3.scaleLinear().domain([0, maxVal]).range([props.height, 0]); // Invert Y for SVG

  const lineGenerator = d3
    .line<number>()
    .x((d, i) => xScale(i))
    .y((d) => yScale(d))
    .curve(d3.curveMonotoneX); // Smooth curve? Or linear? User asked for simplicity. Monotone is nice.

  return lineGenerator(data) || "";
});

// ASCII Computation
const asciiChart = computed(() => {
  if (props.lib !== "ascii" || !props.data.length) return "";
  // simple-ascii-chart config
  // It returns a string.
  // We need to configure it to fit roughly?
  // It usually takes an array.
  try {
    return plot(props.data, {
      height: Math.min(10, Math.floor(props.height / 4)), // approx lines?
      min: 0,
    });
  } catch (e) {
    return "Error generating ASCII chart";
  }
});
</script>

<template>
  <div class="w-full h-full">
    <!-- D3 Render -->
    <svg
      v-if="lib === 'd3'"
      :viewBox="`0 0 ${width} ${height}`"
      preserveAspectRatio="none"
      class="w-full h-full overflow-visible"
    >
      <path
        :d="d3Path"
        fill="none"
        :stroke="color"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        vector-effect="non-scaling-stroke"
      />
    </svg>

    <!-- ASCII Render -->
    <pre
      v-else
      class="font-mono text-xs leading-none overflow-hidden select-none whitespace-pre"
      :style="{ color: color }"
      >{{ asciiChart }}</pre
    >
  </div>
</template>
