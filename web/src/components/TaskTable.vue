<template>
  <MotionConfig :reduced-motion="store?.motion ? 'always' : 'never'">
    <TaskNew v-if="showTaskNew" />

    <!-- tab -->
    <div class="">
      <button>未开始</button>
      <button>进行中</button>
      <button>已完成</button>
    </div>
    <!-- row -->
    <!-- operations -->
    <div class="">
      <button @click="showTaskNew = !showTaskNew">+ New</button>
      <button @click="console.debug(123)">▶</button>
      <button>⏸</button>
      <button>🗑</button>
      <input placeholder="Search">🔍</input>
    </div>
  </MotionConfig>
</template>
<script lang="ts" setup>
import { onMounted, reactive, ref } from "vue";
import { MotionConfig, motion, motionValue } from "motion-v";
import { useStore } from "../store/settings";
import TaskNew from "./TaskNew.vue";
const store = ref<ReturnType<typeof useStore>>();
onMounted(() => {
  store.value = useStore();
});
const showTaskNew = ref(true);
</script>
<style scoped>
</style>