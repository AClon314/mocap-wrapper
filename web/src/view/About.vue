<template>
  <MarkdownRender :content="md" />
</template>
<script setup lang="ts">
import MarkdownRender from 'markstream-vue'
import 'markstream-vue/index.css'
import md from '@/../README.md?raw'
</script>
