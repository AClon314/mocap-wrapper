<template>
  {{ t('task queue') }}
  vue good table https://borisflesch.github.io/vue-good-table-next/guide/#installation https://github.com/borisflesch/vue-good-table-next 支持静态渲染
  vue3-table-lite  https://vue3-lite-table.vercel.app/simple-examples.html https://github.com/linmasahiro/vue3-table-lite 部分支持静态渲染
  <!-- TODO TUI都不支持动态切换 -->
  <TaskRow />
</template>

<script setup lang="ts">
import TaskRow from '@/components/TaskRow.vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const tasks = [{}]
</script>
