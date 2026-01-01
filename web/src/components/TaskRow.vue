<template>
  <MotionConfig :reduced-motion="store?.motion ? 'always' : 'never'">
    
  </MotionConfig>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { MotionConfig, motion, motionValue } from "motion-v";
import { useStore } from "../store/settings";
const store = ref<ReturnType<typeof useStore>>();
onMounted(() => {
  store.value = useStore();
});
</script>

<style scoped>
</style>
