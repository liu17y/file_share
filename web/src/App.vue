<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // 初始化暗色模式
  const darkMode = localStorage.getItem('dark_mode') === 'true'
  if (darkMode) {
    document.documentElement.classList.add('dark')
  }
})
</script>

<style>
#app {
  min-height: 100vh;
}
</style>