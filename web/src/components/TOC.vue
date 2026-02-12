<!-- 目录按钮 -->
<template>
  <nav class="flex flex-col z-30 fixed bottom-0" aria-label="导航目录">
    <RouterLink
      v-for="r in routes"
      :key="r.name"
      :to="r.path"
      :aria-current-value="isCurrent ? 'page' : null"
      aria-label="使用中文"
      tabindex="-1"
    >
      <button :class="{ active: r.path === route.path }">
        {{ t((r.meta.title as string) ?? r.name) }}
      </button>
    </RouterLink>
  </nav>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const route = useRoute()
const isCurrent = computed(() => route.path === route.path)
const router = useRouter()
const _routes = router.getRoutes()
const routes = _routes.slice(
  0,
  _routes.findIndex((r) => r.path === '/'),
)
</script>
