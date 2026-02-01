<template>
  <div v-bind="api.getRootProps()">
    <!-- <a href="#toc" class="absolute z-50">跳至主导航</a>
    <a href="#main" class="absolute z-50">跳至内容</a> -->

    <header v-bind="api.getPanelProps({ id: 'toc' })">
      <TOC></TOC>
    </header>
    <div class="w-1 invert" v-bind="api.getResizeTriggerProps({ id: 'toc:main' })" />
    <main v-bind="api.getPanelProps({ id: 'main' })">
      <!-- <section aria-labelledby="form-heading"></section> -->
      <RouterView></RouterView>
    </main>
    <!-- <footer>
      <small>© 2026 AClon314</small>
    </footer> -->
  </div>
</template>
<script setup lang="ts">
import { watchEffect } from 'vue'
import { useOrientStore } from './store/orient'
import TOC from './components/TOC.vue'

import * as splitter from '@zag-js/splitter'
import { normalizeProps, useMachine } from '@zag-js/vue'
import { computed } from 'vue'
const service = useMachine(splitter.machine, {
  id: '1',
  defaultSize: [20, 80],
  panels: [
    { id: 'toc', minSize: 5 },
    { id: 'main', minSize: 10 },
  ],
})
const api = computed(() => splitter.connect(service, normalizeProps))

const orient = useOrientStore()
watchEffect(() => {
  document.body.style.setProperty('--angle', orient.smooth.theta.toFixed(2))
})
</script>
