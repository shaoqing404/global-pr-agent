<script setup>
import { ref } from 'vue'

const emit = defineEmits(['select'])
const inputKey = ref('')
const showKeyInput = ref(false)

const startDemo = () => {
  emit('select', 'demo')
}

const startProd = () => {
  if (inputKey.value.trim()) {
    emit('select', 'prod', inputKey.value.trim())
  }
}
</script>

<template>
  <div class="h-full flex items-center justify-center p-6">
    <div class="max-w-4xl w-full">
      <div class="text-center mb-12">
        <h2 class="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">欢迎使用 Global PR Agent</h2>
        <p class="text-gray-400 text-lg">请选择您的系统运行模式</p>
      </div>

      <div class="grid md:grid-cols-2 gap-6">
        <!-- Demo Mode Card -->
        <div 
          @click="startDemo"
          class="bg-[#161b22] border border-gray-800 hover:border-blue-500/50 rounded-xl p-8 cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-blue-900/20 group relative overflow-hidden"
        >
          <div class="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="text-4xl mb-4">💡</div>
          <h3 class="text-xl font-semibold mb-3 text-gray-200">AITO 场景演示 (AITO Scenario)</h3>
          <p class="text-gray-400 text-sm leading-relaxed mb-4">
            该模式下，我们将直接使用预置的《问界 / AITO 在阿联酋市场的 DeepResearch 研究报告》作为知识输入，模拟真实项目中耗时的信息收集阶段。后续的澄清反问、战略洞察、内容生成、多专家审定和多语言反馈，均由真实大模型实时推理生成。
          </p>
          <ul class="text-xs text-gray-500 space-y-2">
            <li class="flex items-center gap-2"><span class="text-blue-400">✓</span> 使用后端默认配置的 LLM (真实推理)</li>
            <li class="flex items-center gap-2"><span class="text-blue-400">✓</span> 预置市场战略底座</li>
            <li class="flex items-center gap-2"><span class="text-blue-400">✓</span> 适合快速体验 Agent 全工作流</li>
          </ul>
        </div>

        <!-- Prod Mode Card -->
        <div 
          class="bg-[#161b22] border border-gray-800 hover:border-purple-500/50 rounded-xl p-8 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-900/20 relative overflow-hidden"
        >
          <div class="text-4xl mb-4">🚀</div>
          <h3 class="text-xl font-semibold mb-3 text-gray-200">生产模式 (Production)</h3>
          <p class="text-gray-400 text-sm leading-relaxed mb-6">
            系统将全面激活基于 FastAPI 的 Agentic Workflow。支持用户自定义上传市场研究文档，由大语言模型执行动态的情报解析、战略推演与多语言智能生成。
          </p>
          
          <div v-if="!showKeyInput" class="mt-auto">
            <button @click="showKeyInput = true" class="w-full py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors border border-gray-700">
              配置授权并进入
            </button>
          </div>
          
          <div v-else class="space-y-3 mt-auto animate-fade-in">
            <label class="text-xs text-gray-400 font-medium">System Access Token</label>
            <div class="flex gap-2">
              <input 
                v-model="inputKey" 
                type="password" 
                placeholder="Enter your DEMO_ACCESS_TOKEN" 
                class="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50"
                @keyup.enter="startProd"
              >
              <button 
                @click="startProd"
                :disabled="!inputKey.trim()"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              >
                进入
              </button>
            </div>
            <p class="text-[10px] text-gray-500">注：当前后端已配置默认 LLM Key，此处为系统防护 Token。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
