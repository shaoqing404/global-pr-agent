<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import WelcomeScreen from './components/WelcomeScreen.vue'
import ChatInterface from './components/ChatInterface.vue'

const appMode = ref(null) // 'demo' | 'prod' | null
const apiKey = ref('')

const handleModeSelect = (mode, key = '') => {
  appMode.value = mode
  if (mode === 'prod') {
    apiKey.value = key
    axios.defaults.headers.common['ACCESS_TOKEN'] = key
  }
}
</script>

<template>
  <div class="h-screen w-full flex flex-col bg-[#0d1117] overflow-hidden">
    <header class="h-14 border-b border-gray-800 bg-[#161b22] flex items-center px-6 justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <span class="text-xl">🌍</span>
        <h1 class="text-lg font-semibold text-gray-200 tracking-wide">Global PR Agent</h1>
      </div>
      <div class="flex items-center gap-4">
        <a href="/docs/interactive_design.html" target="_blank" class="text-xs px-3 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-md text-white font-medium transition-all shadow-lg">
          ✨ 交互式架构文档
        </a>
        <div v-if="appMode" class="text-xs px-2 py-1 rounded-md" :class="appMode === 'prod' ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-blue-900/50 text-blue-400 border border-blue-800'">
          {{ appMode === 'prod' ? '生产模式 (Production)' : '演示模式 (Demo Fallback)' }}
        </div>
      </div>
    </header>

    <main class="flex-1 overflow-hidden relative">
      <Transition name="fade" mode="out-in">
        <WelcomeScreen v-if="!appMode" @select="handleModeSelect" />
        <ChatInterface v-else :mode="appMode" :apiKey="apiKey" />
      </Transition>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
