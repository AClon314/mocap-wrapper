<template>
  {{ id }}
  {{ progress }}
  {{ title }}
  {{ input }}
  {{ output }}
  {{ size }}
  {{ speed }}
  {{ ETA }}
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
// import { useStore } from '../store/settings'
// const store = ref<ReturnType<typeof useStore>>()
// onMounted(() => {
//   store.value = useStore()
// })

const pros = defineProps({
  id: {
    type: Number,
  },
  progress: {
    type: Number,
  },
  title: {
    type: String,
  },
  input: {
    type: Array<string>,
  },
  output: {
    type: Array<string>,
  },
  size: {
    type: String,
  },
})
const speed = computed(() => {
  return Math.round(pros.progress * 100)
})
const ETA = computed(() => {
  return Math.round(pros.progress * 100)
})
defineExpose({ speed, ETA })
</script>

<style scoped></style>
