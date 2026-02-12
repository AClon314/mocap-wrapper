<template>
  Component test
  <button>Start</button>
  <button class="primary">Start</button>
  <label>
    <input type="checkbox">
    Label
  </label>
  <input type="range" min="0" max="100" v-model="v">{{ v }}</input>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue';

const v = ref(0)
watchEffect(() => {
  document.body.style.setProperty('--debug', `${v.value / 200}ch`)
})
</script>
