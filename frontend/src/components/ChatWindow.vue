<template>
  <div class="chat-container">
    <!-- 头部 -->
    <div class="chat-header">
      <h2>🤖 Agent 助手</h2>
      <div class="status">
        <span :class="['status-dot', isConnected ? 'connected' : 'disconnected']"></span>
        {{ isConnected ? '已连接' : '未连接' }}
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(msg, idx) in messages" :key="idx" class="message-wrapper">
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="message user">
          <div class="message-content">{{ msg.content }}</div>
          <div class="message-time">{{ msg.time }}</div>
        </div>

        <!-- Assistant 消息 -->
        <div v-else-if="msg.role === 'assistant'" class="message assistant">
          <div class="message-content">
            <div v-html="formatMessage(msg.content)"></div>
            <span v-if="msg.streaming" class="cursor">▌</span>
          </div>
          <div class="message-time">{{ msg.time }}</div>

          <!-- 中间步骤（可折叠） -->
          <div v-if="msg.steps && msg.steps.length > 0" class="steps">
            <div class="steps-header" @click="msg.stepsCollapsed = !msg.stepsCollapsed">
              <span>{{ msg.stepsCollapsed ? '▶' : '▼' }}</span>
              <span>执行步骤 ({{ msg.steps.length }})</span>
            </div>
            <div v-show="!msg.stepsCollapsed" class="steps-content">
              <div v-for="(step, stepIdx) in msg.steps" :key="stepIdx" :class="['step', step.type]">
                <span class="step-icon">
                  {{
                    step.type === 'thinking'
                      ? '💭'
                      : step.type === 'tool_call'
                        ? '🔧'
                        : step.type === 'tool_result'
                          ? '📋'
                          : '📄'
                  }}
                </span>
                <span class="step-text">{{ step.content }}</span>
                <span v-if="step.args" class="step-args">{{ JSON.stringify(step.args) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 系统消息 -->
        <div v-else-if="msg.role === 'system'" class="message system">
          <div class="message-content">{{ msg.content }}</div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <textarea
        v-model="inputMessage"
        @keydown.enter.prevent="sendMessage"
        placeholder="输入消息... (Enter 发送)"
        :disabled="!isConnected || isProcessing"
        rows="3"
      ></textarea>
      <button
        @click="sendMessage"
        :disabled="!isConnected || !inputMessage.trim() || isProcessing"
        class="send-btn"
      >
        {{ isProcessing ? '处理中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

interface MessageStep {
  type: 'thinking' | 'tool_call' | 'tool_result'
  content: string
  tool?: string
  args?: any
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  time: string
  streaming?: boolean
  steps?: MessageStep[]
  stepsCollapsed?: boolean
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isConnected = ref(false)
const isProcessing = ref(false)
let ws: WebSocket | null = null
let sessionId: string
let currentAssistantMessage: Message | null = null

// 生成会话ID
const generateSessionId = () => {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// 添加消息
const addMessage = (role: 'user' | 'assistant' | 'system', content: string) => {
  const msg: Message = {
    role,
    content,
    time: new Date().toLocaleTimeString(),
    streaming: role === 'assistant',
    steps: [],
    stepsCollapsed: true,
  }
  messages.value.push(msg)

  if (role === 'assistant') {
    currentAssistantMessage = msg
  }

  nextTick(() => {
    const container = document.querySelector('.chat-messages')
    if (container) container.scrollTop = container.scrollHeight
  })

  return msg
}

// 添加步骤到当前消息
const addStep = (type: MessageStep['type'], content: string, tool?: string, args?: any) => {
  if (currentAssistantMessage) {
    if (!currentAssistantMessage.steps) currentAssistantMessage.steps = []
    currentAssistantMessage.steps.push({ type, content, tool, args })

    nextTick(() => {
      const container = document.querySelector('.chat-messages')
      if (container) container.scrollTop = container.scrollHeight
    })
  }
}

// 格式化消息
const formatMessage = (content: string) => {
  if (!content) return ''
  return content
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

// 完成当前消息
const finishCurrentMessage = () => {
  if (currentAssistantMessage) {
    currentAssistantMessage.streaming = false
    currentAssistantMessage = null
  }
  isProcessing.value = false
}

// 连接 WebSocket
const connectWebSocket = () => {
  const userId = localStorage.getItem('user_id') || 'user_' + Date.now()
  localStorage.setItem('user_id', userId)
  sessionId = generateSessionId()

  ws = new WebSocket(`ws://localhost:8000/ws/chat`)

  ws.onopen = () => {
    console.log('WebSocket 连接成功')
    isConnected.value = true

    ws?.send(
      JSON.stringify({
        session_id: sessionId,
        user_id: userId,
      }),
    )

    addMessage('system', '✅ 连接成功，可以开始对话')
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log('收到消息:', data)

    switch (data.type) {
      // ========== 消息生命周期 ==========
      case 'message_start':
        isProcessing.value = true
        addMessage('assistant', '')
        console.log('消息开始:', data.message)
        break

      case 'message_delta':
        console.log('消息更新:', data.delta)
        // 可以处理 stop_reason 等，暂不需要 UI 更新
        break

      case 'message_stop':
        finishCurrentMessage()
        console.log('消息结束')
        break

      // ========== 内容块事件 ==========
      case 'content_block_start':
        if (data.content_block?.type === 'tool_use') {
          addStep('thinking', `准备调用工具: ${data.content_block.name}`)
        }
        break

      case 'content_block_delta':
        console.log(`接收: ${data.delta?.text}, 时间: ${Date.now()}`)  
      
        // 文本增量 → 追加到消息内容
        if (data.delta?.type === 'text_delta' && currentAssistantMessage) {
          currentAssistantMessage.content += data.delta.text
          nextTick(() => {
            const container = document.querySelector('.chat-messages')
            if (container) container.scrollTop = container.scrollHeight
          })
        }
        // 工具参数增量（忽略，因为 tool_use 事件会包含完整参数）
        break

      case 'content_block_stop':
        // 内容块结束，通常不需要处理
        break

      // ========== 工具调用 ==========
      case 'tool_use':
        addStep('tool_call', `调用工具: ${data.name}`, data.name, data.input)
        break

      case 'tool_result':
        const resultPreview = data.content ? data.content.substring(0, 200) : '(无输出)'
        addStep(
          'tool_result',
          `结果: ${resultPreview}${data.content && data.content.length > 200 ? '...' : ''}`,
        )
        break

      // ========== 错误 ==========
      case 'error':
        addMessage('system', `❌ 错误: ${data.content}`)
        finishCurrentMessage()
        break

      default:
        console.log('未处理的事件类型:', data.type, data)
        break
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
    addMessage('system', '❌ 连接错误')
  }

  ws.onclose = () => {
    console.log('WebSocket 连接关闭')
    isConnected.value = false
    isProcessing.value = false
    addMessage('system', '⚠️ 连接断开，3秒后重连...')
    setTimeout(connectWebSocket, 3000)
  }
}

// 发送消息
const sendMessage = () => {
  const message = inputMessage.value.trim()
  if (!message || !ws || ws.readyState !== WebSocket.OPEN || isProcessing.value) return

  addMessage('user', message)

  ws.send(
    JSON.stringify({
      message: message,
      user_id: localStorage.getItem('user_id'),
      session_id: sessionId,
    }),
  )

  inputMessage.value = ''
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
  background: #f5f5f5;
}

.chat-header {
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chat-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.connected {
  background: #4caf50;
  box-shadow: 0 0 4px #4caf50;
}

.status-dot.disconnected {
  background: #f44336;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f9f9f9;
}

.message-wrapper {
  margin-bottom: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.message.user {
  align-items: flex-end;
  margin-left: auto;
}

.message.assistant {
  align-items: flex-start;
  margin-right: auto;
}

.message.system {
  align-items: center;
  margin: 0 auto;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.5;
}

.message.user .message-content {
  background: #007bff;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: white;
  border: 1px solid #e0e0e0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message.system .message-content {
  background: #fff3cd;
  border: 1px solid #ffeeba;
  color: #856404;
  font-size: 12px;
  padding: 6px 12px;
}

.message-time {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
  margin-left: 8px;
  margin-right: 8px;
}

.cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: #007bff;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

.steps {
  margin-top: 8px;
  font-size: 12px;
  background: #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
}

.steps-header {
  padding: 6px 10px;
  background: #e8e8e8;
  cursor: pointer;
  user-select: none;
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 11px;
  color: #666;
}

.steps-header:hover {
  background: #e0e0e0;
}

.steps-content {
  padding: 8px 10px;
  border-top: 1px solid #e0e0e0;
  max-height: 300px;
  overflow-y: auto;
}

.step {
  padding: 4px 0;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 11px;
  border-bottom: 1px solid #e8e8e8;
}

.step:last-child {
  border-bottom: none;
}

.step-icon {
  font-size: 12px;
}

.step-text {
  flex: 1;
  color: #555;
  word-break: break-all;
}

.step-args {
  font-size: 10px;
  color: #888;
  font-family: monospace;
  margin-left: 8px;
}

.step.thinking .step-text {
  color: #856404;
}

.step.tool_call .step-text {
  color: #0c5460;
}

.step.tool_result .step-text {
  color: #155724;
}

.chat-input {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.4;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input textarea:focus {
  border-color: #007bff;
}

.send-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
  height: 44px;
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>