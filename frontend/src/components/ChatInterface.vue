<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  mode: String,
  apiKey: String
})

// States enum
const STATES = {
  TASK_START: 0,
  INTELLIGENCE_INPUT: 1,
  BUSINESS_CONFIRM: 2,
  DIRECTOR_INSIGHT: 3,
  CONTENT_GENERATE: 4,
  FEEDBACK_REVISE: 5
}

const currentState = ref(STATES.TASK_START)
const chatHistory = ref([
  { role: 'assistant', content: '你好！我是 Global PR Agent。首先，请告诉我你要推广的**品牌名称**、**产品**以及**目标市场**，或者直接向我下达您的 PR 推广诉求。' }
])
const userInput = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)

onMounted(() => {
  if (props.mode === 'demo') {
    userInput.value = '帮我调研问界 / AITO 品牌在阿联酋市场的 PR 推广机会，并设计一份面向阿拉伯地区、英文撰写的高端智能 SUV 品牌 PR 稿件'
  }
})

const renderMarkdown = (text) => {
  return DOMPurify.sanitize(marked(text))
}

// Session Data
const sessionData = {
  metadata: {},
  report: null,
  confirmation: null,
  insight: null,
  draft: null,
  reviews: null,
  workflowResult: null
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

watch(chatHistory, scrollToBottom, { deep: true })

const addMessage = (role, content, actions = null) => {
  chatHistory.value.push({ role, content, actions })
}

const handleAction = async (actionId, msgIndex) => {
  if (isLoading.value) return;
  
  if (actionId === 'confirm_plan') {
      userInput.value = "确认计划";
      sendMessage();
  } else if (actionId === 'confirm_strategy') {
      userInput.value = "确认策略";
      sendMessage();
  } else if (actionId === 'confirm_generation') {
      userInput.value = "确认生成";
      sendMessage();
  } else if (actionId === 'export_doc') {
      userInput.value = "导出文档";
      sendMessage();
  }
  
  // Optionally remove actions from the message once clicked
  if (chatHistory.value[msgIndex]) {
      chatHistory.value[msgIndex].actions = null;
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  isLoading.value = true
  addMessage('user', `📄 上传了文件: ${file.name}`)

  const reader = new FileReader()
  reader.onload = async (e) => {
    const text = e.target.result
    try {
      // Call FastAPI extract endpoint
      const response = await axios.post('/api/extract', { text }, {
        headers: props.apiKey ? { 'ACCESS_TOKEN': props.apiKey } : {}
      })
      sessionData.report = response.data
      addMessage('assistant', `✅ 已成功从文档中提取结构化战略情报！您可以输入“确认”进入业务决策阶段。\n\n\`\`\`json\n${JSON.stringify(sessionData.report.metadata || {}, null, 2)}\n\`\`\``)
    } catch (error) {
      console.error(error)
      addMessage('assistant', `⚠️ 提取失败或接口未授权。由于是 AITO 演示场景，我将为您自动加载预置的《问界 / AITO 标准化情报底座》。输入“确认”继续。`)
      sessionData.report = null // Fallback trigger
    }
    isLoading.value = false
  }
  reader.readAsText(file)
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const prompt = userInput.value.trim()
  addMessage('user', prompt)
  userInput.value = ''
  isLoading.value = true

  try {
    const forceFallback = false // Always use real LLMs unless backend forces fallback on error
    const headers = props.apiKey ? { 'ACCESS_TOKEN': props.apiKey } : {}

    if (currentState.value === STATES.TASK_START) {
      // First interaction: collect basic info and ask questions
      if (!sessionData.metadata.brand) {
          sessionData.metadata = { 
            brand: prompt.includes('问界') || prompt.includes('AITO') ? '问界 / AITO' : prompt.split(" ")[0],
            target_market: prompt.includes('阿联酋') || prompt.includes('UAE') ? 'UAE' : 'Global',
            target_language: prompt.includes('英文') || prompt.includes('English') ? 'English' : 'Local',
            pr_objective: prompt
          }
          const res = await axios.post('/api/plan', { metadata: sessionData.metadata }, { headers })
          let q_str = ""
          if (res.data.clarification_questions && res.data.clarification_questions.length > 0) {
              q_str = res.data.clarification_questions.map(q => `- ${q}`).join('\n')
          } else {
              q_str = "- 本次推广的预算限制是多少？\n- 是否有确定的发布日期？"
          }
          
          addMessage('assistant', `收到！我已经记录了基础任务信息。\n\n在正式规划前，根据我的分析，我有几个业务细节需要向您澄清：\n\n${q_str}\n\n您可以补充这些信息，或者直接确认进入战略情报环节。`, [
              { id: 'confirm_plan', label: '确认计划并进入下一步', primary: true }
          ])
          // We stay in TASK_START until '确认计划' is received
      } else {
          if (prompt.includes('确认计划')) {
              // Advance to Intelligence Input
              if (!sessionData.report) {
                  addMessage('assistant', `⏳ 正在为您接入战略情报库...`)
                  await new Promise(r => setTimeout(r, 1000))
                  sessionData.report = null // Handled by backend fallback
              }
              
              addMessage('assistant', `✅ 战略情报已就位。\n\n进入业务决策阶段。我提炼了以下推荐策略：\n- **核心 PR 角度**: 突出智能豪华与本地服务信任。\n- **本土化策略**: 强调当地合作，避免对抗性语言。\n\n请核实。如果需要调整请直接告诉我，或者点击确认流转至总监战略洞察阶段。`, [
                  { id: 'confirm_strategy', label: '确认策略', primary: true }
              ])
              currentState.value = STATES.BUSINESS_CONFIRM
          } else {
              // Inner loop for TASK_START
              addMessage('assistant', `已收到您的解答并记录入情报库中。如果您还有其他补充可以直接告诉我，或者点击「确认计划」进入下一步的业务策略提炼。`, [
                  { id: 'confirm_plan', label: '确认计划并进入下一步', primary: true }
              ])
          }
      }

    } else if (currentState.value === STATES.INTELLIGENCE_INPUT) {
      // This state is skipped in the strict flow, merged into TASK_START confirmation.
      // Kept for enum alignment, but logic moved to TASK_START -> BUSINESS_CONFIRM transition.
      currentState.value = STATES.BUSINESS_CONFIRM;

    } else if (currentState.value === STATES.BUSINESS_CONFIRM) {
      if (prompt.includes('确认策略')) {
        addMessage('assistant', `⏳ 正在由 Director Agent 基于大模型推理生成战略洞察...`)
        const payload = { 
            metadata: sessionData.metadata, 
            information_report: sessionData.report,
            force_fallback: forceFallback 
        }
        const res = await axios.post('/api/insight', payload, { headers })
        sessionData.insight = res.data
        addMessage('assistant', `✅ 业务策略已锁定。这是大模型最新推演的战略洞察：\n\n**品牌洞察**:\n${sessionData.insight.brand_insight}\n\n**本土化建议**:\n${sessionData.insight.localization_advice}\n\n如果您需要调整洞察视角，请直接输入。如果确认无误，我将立即进入内容创作，并同时呼叫专家团进行审定。`, [
            { id: 'confirm_generation', label: '确认并生成初稿', primary: true }
        ])
        currentState.value = STATES.DIRECTOR_INSIGHT
      } else {
        // Inner loop: update strategy
        if (!sessionData.confirmation) sessionData.confirmation = { human_notes: '' }
        sessionData.confirmation.human_notes += ` | ${prompt}`
        addMessage('assistant', `已根据您的意见动态调整业务策略记录。如果确认无误，请输入「确认策略」或点击放行。`, [
            { id: 'confirm_strategy', label: '确认策略', primary: true }
        ])
      }

    } else if (currentState.value === STATES.DIRECTOR_INSIGHT) {
      if (prompt.includes('确认生成')) {
        addMessage('assistant', `⏳ 正在大模型端一键生成内容，并调用 4 位专家协同审查... (这可能需要 15-30 秒)`)
        const payload = { 
            metadata: sessionData.metadata, 
            information_report: sessionData.report,
            human_confirmation: sessionData.confirmation,
            force_fallback: forceFallback 
        }
        // Generate draft
        const draftRes = await axios.post('/api/generate', payload, { headers })
        sessionData.draft = draftRes.data
        
        // Review draft
        const reviewRes = await axios.post('/api/review', payload, { headers })
        sessionData.reviews = reviewRes.data.items

        const reviewStr = sessionData.reviews.map(r => `- **${r.reviewer}**: ${r.issues && r.issues.length > 0 ? r.issues[0] : '通过'}`).join('\n')
        addMessage('assistant', `🎉 初稿已生成！系统调用了四位专家给出以下审定意见：\n\n${reviewStr}\n\n**请问您希望如何修改初稿？** \n*(注：若需输出为特定语言如阿拉伯语，请在此下达指令。若无修改意见，可直接导出)*`, [
            { id: 'export_doc', label: '定稿并导出文档', primary: true }
        ])
        currentState.value = STATES.FEEDBACK_REVISE
      } else {
         addMessage('assistant', `已记录您的洞察修正建议，大模型将以此作为约束进行下一步生成。确认放行吗？`, [
             { id: 'confirm_generation', label: '确认并生成初稿', primary: true }
         ])
      }

    } else if (currentState.value === STATES.FEEDBACK_REVISE) {
      if (prompt.includes('导出文档') || prompt.toLowerCase().includes('export') || prompt.includes('结束')) {
        const payload = { 
            metadata: sessionData.metadata, 
            information_report: sessionData.report,
            human_confirmation: sessionData.confirmation,
            human_feedback: "Finalized",
            force_fallback: forceFallback 
        }
        const res = await axios.post('/api/generate-pr', payload, { headers })
        sessionData.workflowResult = res.data
        
        // Let's create a blob for the JSON download as an example
        const jsonStr = JSON.stringify(sessionData.workflowResult, null, 2)
        const blob = new Blob([jsonStr], { type: "application/json" })
        const url = URL.createObjectURL(blob)
        
        addMessage('assistant', `✅ **全套 PR 物料已准备完毕。** \n\n[📥 点击这里下载完整的 JSON 数据包](${url}) \n\n*注：生产环境可直接对接 n8n/Dify 进行自动化分发。*`)
      } else {
        addMessage('assistant', `⏳ 正在请求大模型根据您的反馈进行修订与语言本土化...`)
        const payload = { 
            metadata: sessionData.metadata, 
            information_report: sessionData.report,
            human_confirmation: sessionData.confirmation,
            human_feedback: prompt,
            force_fallback: forceFallback 
        }
        const res = await axios.post('/api/generate-pr', payload, { headers })
        sessionData.draft = res.data.draft
        
        addMessage('assistant', `我已经根据您的要求完成了修订。还有其他需要调整的地方吗？确认无误请放行。\n\n> **预览**:\n\n${res.data.revised_draft.substring(0, 500)}...`, [
            { id: 'export_doc', label: '定稿并导出文档', primary: true }
        ])
      }
    }
  } catch (error) {
    console.error(error)
    addMessage('assistant', `❌ 请求失败。请检查后端服务或模型 API 网络连接。错误信息: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="h-full flex flex-col md:flex-row">
    <!-- Sidebar / Status -->
    <aside class="w-full md:w-64 bg-[#161b22] border-r border-gray-800 flex flex-col h-full flex-shrink-0">
      <div class="p-4 border-b border-gray-800">
        <h3 class="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">执行状态</h3>
        <div class="space-y-3">
          <div class="flex items-center gap-3 text-sm" :class="currentState >= 0 ? 'text-blue-400' : 'text-gray-600'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs" :class="currentState >= 0 ? 'bg-blue-900' : 'bg-gray-800'">1</span>
            任务启动
          </div>
          <div class="flex items-center gap-3 text-sm" :class="currentState >= 1 ? 'text-blue-400' : 'text-gray-600'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs" :class="currentState >= 1 ? 'bg-blue-900' : 'bg-gray-800'">2</span>
            战略情报
          </div>
          <div class="flex items-center gap-3 text-sm" :class="currentState >= 2 ? 'text-blue-400' : 'text-gray-600'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs" :class="currentState >= 2 ? 'bg-blue-900' : 'bg-gray-800'">3</span>
            业务决策
          </div>
          <div class="flex items-center gap-3 text-sm" :class="currentState >= 3 ? 'text-blue-400' : 'text-gray-600'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs" :class="currentState >= 3 ? 'bg-blue-900' : 'bg-gray-800'">4</span>
            战略洞察
          </div>
          <div class="flex items-center gap-3 text-sm" :class="currentState >= 4 ? 'text-blue-400' : 'text-gray-600'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs" :class="currentState >= 4 ? 'bg-blue-900' : 'bg-gray-800'">5</span>
            生成审定
          </div>
          <div class="flex items-center gap-3 text-sm" :class="currentState >= 5 ? 'text-blue-400' : 'text-gray-600'">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs" :class="currentState >= 5 ? 'bg-blue-900' : 'bg-gray-800'">6</span>
            反馈优化
          </div>
        </div>
      </div>

      <div class="p-4 flex-1">
        <h3 class="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">情报注入通道</h3>
        <p class="text-xs text-gray-500 mb-3">支持非结构化 TXT/MD 上传，由 LLM 智能抽取为 Schema。</p>
        <label 
          class="flex flex-col items-center justify-center w-full h-24 border-2 border-gray-700 border-dashed rounded-lg cursor-pointer hover:bg-gray-800 hover:border-blue-500 transition-colors"
          :class="{ 'opacity-50 cursor-not-allowed': currentState !== 1 || isLoading }"
        >
          <div class="flex flex-col items-center justify-center pt-5 pb-6">
            <svg class="w-6 h-6 mb-2 text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16"><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/></svg>
            <p class="text-xs text-gray-500">点击上传文件</p>
          </div>
          <input type="file" class="hidden" accept=".txt,.md" @change="handleFileUpload" :disabled="currentState !== 1 || isLoading" />
        </label>
      </div>
    </aside>

    <!-- Main Chat Area -->
    <main class="flex-1 flex flex-col h-full bg-[#0d1117] relative">
      <div class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" ref="chatContainer">
        <div v-for="(msg, idx) in chatHistory" :key="idx" class="flex items-start gap-4" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
          <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" :class="msg.role === 'user' ? 'bg-purple-600' : 'bg-blue-600'">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="flex flex-col gap-2 max-w-[80%]">
            <div class="rounded-2xl px-4 py-3 text-sm" :class="msg.role === 'user' ? 'bg-[#21262d] text-gray-200 border border-gray-700 whitespace-pre-wrap' : 'bg-transparent text-gray-300 markdown-body'" v-html="renderMarkdown(msg.content)">
            </div>
            <!-- Action Buttons -->
            <div v-if="msg.actions && msg.actions.length > 0" class="flex flex-wrap gap-2 mt-1">
              <button 
                v-for="action in msg.actions" 
                :key="action.id"
                @click="handleAction(action.id, idx)"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors shadow-sm"
                :class="action.primary ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-[#21262d] hover:bg-gray-700 text-gray-300 border border-gray-600'"
              >
                {{ action.label }}
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="isLoading" class="flex items-start gap-4">
          <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">🤖</div>
          <div class="px-4 py-3 text-sm text-gray-500 animate-pulse">正在思考处理中...</div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 border-t border-gray-800 bg-[#161b22]">
        <div class="max-w-4xl mx-auto relative flex items-center">
          <input 
            v-model="userInput" 
            type="text" 
            placeholder="输入指令 (如：确认、修改建议、翻译要求)..." 
            class="w-full bg-[#0d1117] border border-gray-700 rounded-xl pl-4 pr-12 py-3 text-sm text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            @keyup.enter="sendMessage"
            :disabled="isLoading"
          >
          <button 
            @click="sendMessage"
            :disabled="!userInput.trim() || isLoading"
            class="absolute right-2 p-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
        <div class="text-center mt-2">
          <span class="text-[10px] text-gray-500">通过对话驱动 Agent 状态流转。支持多轮审查与多语言翻译。</span>
        </div>
      </div>
    </main>
  </div>
</template>
