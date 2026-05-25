<template>
  <div class="app">
    <!-- 准备阶段：填写信息 -->
    <div v-if="phase === 'prepare'" class="prepare-phase">
      <div class="prepare-card">
        <h1>AI 模拟面试</h1>
        <p class="subtitle">智能面试官 + 数字人播报</p>

        <div class="form-item">
          <label>面试岗位</label>
          <select v-model="form.position">
            <option value="">请选择岗位</option>
            <option value="前端开发">前端开发</option>
            <option value="后端开发">后端开发</option>
            <option value="全栈开发">全栈开发</option>
            <option value="产品经理">产品经理</option>
            <option value="数据分析师">数据分析师</option>
          </select>
        </div>

        <div class="form-item">
          <label>简历上传</label>
          <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
            <input
              type="file"
              ref="fileInput"
              @change="handleFileChange"
              accept=".pdf,.doc,.docx,.txt"
              style="display: none"
            />
            <div v-if="form.resumeFile" class="file-info">
              <span class="file-icon">📄</span>
              <span class="file-name">{{ form.resumeFile.name }}</span>
              <button class="btn-remove" @click.stop="removeFile">×</button>
            </div>
            <div v-else class="upload-placeholder">
              <span class="upload-icon">📎</span>
              <span>点击上传或拖拽简历</span>
              <span class="upload-hint">支持 PDF、Word、TXT 格式</span>
            </div>
          </div>
        </div>

        <button class="btn-primary" @click="startInterview" :disabled="!canStart">
          {{ starting ? '正在开始...' : '开始面试' }}
        </button>
      </div>
    </div>

    <!-- 面试阶段 -->
    <div v-else-if="phase === 'interview'" class="interview-phase">
      <!-- 顶部栏 -->
      <div class="header">
        <div class="header-left">
          <span class="position-tag">{{ session.position }}</span>
          <span class="status">面试进行中</span>
          <span class="round-info">第 {{ currentRound }}/{{ maxRounds }} 轮</span>
        </div>
        <div class="header-right">
          <span v-if="duration" class="duration">⏱ {{ formatDuration(duration) }}</span>
          <button class="btn-text" @click="showEndConfirm = true">结束面试</button>
        </div>
      </div>

      <!-- 数字人区域 -->
      <div class="avatar-section">
        <div class="avatar-box">
          <div class="avatar-display">
            <video
              v-if="currentVideoUrl"
              :src="currentVideoUrl"
              class="avatar-video"
              autoplay
              muted
              @ended="onVideoEnded"
            ></video>
            <div v-else class="avatar-circle">
              <span class="avatar-emoji">👨‍💼</span>
            </div>
            <div v-if="currentAudioUrl && !currentVideoUrl" class="audio-wave">
              <span></span><span></span><span></span><span></span><span></span>
            </div>
            <button v-if="isAudioPlaying" class="btn-stop-audio" @click="stopAudio">停止</button>
          </div>
          <div v-if="currentMessage" class="avatar-speak">
            {{ currentMessage }}
          </div>
        </div>
      </div>

      <!-- 对话区域 -->
      <div class="chat-section">
        <div class="messages" ref="messagesEl">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message', msg.role]"
          >
            <div class="message-avatar">
              {{ msg.role === 'interviewer' ? '👨‍💼' : '👤' }}
            </div>
            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>

          <!-- AI 正在输入 -->
          <div v-if="aiTyping" class="message interviewer">
            <div class="message-avatar">👨‍💼</div>
            <div class="message-content">
              <div class="typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <textarea
            v-model="userInput"
            placeholder="输入你的回答..."
            rows="3"
            :disabled="aiTyping"
            @keydown.enter.exact.prevent="sendAnswer"
          ></textarea>
          <button
            class="btn-send"
            @click="sendAnswer"
            :disabled="!userInput.trim() || aiTyping"
          >
            发送
          </button>
        </div>
      </div>
    </div>

    <!-- 报告阶段 -->
    <div v-else-if="phase === 'report'" class="report-phase">
      <div class="report-card">
        <h2>面试完成</h2>
        <p class="subtitle">以下是您的面试反馈报告</p>

        <div class="score-section">
          <div class="score-circle">
            <span class="score-num">{{ report.overall_score || 0 }}</span>
            <span class="score-max">/10</span>
          </div>
        </div>

        <div class="report-section">
          <h3>💪 优点</h3>
          <ul>
            <li v-for="(item, i) in report.strengths" :key="i">{{ item }}</li>
          </ul>
        </div>

        <div class="report-section">
          <h3>📝 需要改进</h3>
          <ul class="weakness">
            <li v-for="(item, i) in report.weaknesses" :key="i">{{ item }}</li>
          </ul>
        </div>

        <div class="report-section">
          <h3>📊 维度评分</h3>
          <div class="dimensions">
            <div
              v-for="(score, key) in report.detailed_feedback"
              :key="key"
              class="dimension-item"
            >
              <span class="dim-name">{{ key }}</span>
              <div class="dim-bar">
                <div class="dim-fill" :style="{ width: (score / 10 * 100) + '%' }"></div>
              </div>
              <span class="dim-score">{{ score }}</span>
            </div>
          </div>
        </div>

        <button class="btn-primary" @click="resetInterview">再试一次</button>
      </div>
    </div>

    <!-- 结束确认弹窗 -->
    <div v-if="showEndConfirm" class="modal-overlay" @click.self="showEndConfirm = false">
      <div class="modal">
        <h3>确认结束面试？</h3>
        <p>结束面试后将生成反馈报告</p>
        <div class="modal-btns">
          <button class="btn-secondary" @click="showEndConfirm = false">继续面试</button>
          <button class="btn-danger" @click="endInterview">确认结束</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { interviewApi } from './api.js'

// 阶段：prepare | interview | report
const phase = ref('prepare')
const form = ref({ position: '', resumeFile: null })
const starting = ref(false)
const session = ref(null)
const messages = ref([])
const userInput = ref('')
const aiTyping = ref(false)
const currentMessage = ref('')
const report = ref({})
const showEndConfirm = ref(false)
const messagesEl = ref(null)
const fileInput = ref(null)

// 数字人状态
const currentVideoUrl = ref('')
const currentAudioUrl = ref('')
const currentAvatarId = ref('default')
const isAudioPlaying = ref(false)

// 新增
const currentRound = ref(1)
const maxRounds = ref(10)
const duration = ref(0)
let durationTimer = null

const canStart = computed(() => form.value.position && form.value.resumeFile)

async function startInterview() {
  if (!canStart.value || starting.value) return
  starting.value = true
  stopAudio()

  try {
    // 1. 创建会话（使用 FormData 上传文件）
    const formData = new FormData()
    formData.append('user_id', 'user_' + Date.now())
    formData.append('position', form.value.position)
    formData.append('resume_file', form.value.resumeFile)

    const res = await interviewApi.createSession(formData)
    session.value = res.data

    // 2. 开始面试
    const startRes = await interviewApi.startInterview(session.value.id)

    // 3. 获取消息和状态
    await loadMessages()
    await loadStatus()

    // 4. 进入面试阶段
    phase.value = 'interview'
    startDurationTimer()
  } catch (e) {
    console.error('启动面试失败:', e)
    alert('启动面试失败，请重试')
  } finally {
    starting.value = false
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileChange(e) {
  const file = e.target.files[0]
  if (file) {
    form.value.resumeFile = file
  }
}

function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file) {
    const validTypes = ['.pdf', '.doc', '.docx', '.txt']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (validTypes.includes(ext)) {
      form.value.resumeFile = file
    } else {
      alert('仅支持 PDF、Word、TXT 格式')
    }
  }
}

function removeFile() {
  form.value.resumeFile = null
  if (fileInput.value) fileInput.value.value = ''
}

async function loadMessages() {
  if (!session.value) return
  const res = await interviewApi.getMessages(session.value.id)
  messages.value = res.data
  scrollToBottom()

  // 只处理最后一条面试官消息
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.role === 'interviewer') {
    // 如果新消息和当前消息不同，才生成新的音频
    if (currentMessage.value !== lastMsg.content) {
      currentMessage.value = lastMsg.content
      generateAvatarContent(lastMsg.content)
    }
  }
}

let audioPlayer = null

function stopAudio() {
  if (audioPlayer) {
    audioPlayer.pause()
    audioPlayer.currentTime = 0
    audioPlayer = null
  }
  isAudioPlaying.value = false
  currentAudioUrl.value = ''
  currentVideoUrl.value = ''
}

async function generateAvatarContent(text) {
  if (!text) return
  currentMessage.value = text

  // 停止之前的音频
  stopAudio()

  try {
    // 生成 TTS 音频
    const audioRes = await interviewApi.generateAudio(text)
    if (audioRes.data.audio_url) {
      currentAudioUrl.value = audioRes.data.audio_url

      // 播放音频
      audioPlayer = new Audio(audioRes.data.audio_url)
      audioPlayer.play().catch(() => {})
      isAudioPlaying.value = true

      audioPlayer.onended = () => {
        isAudioPlaying.value = false
      }

      // 尝试生成视频
      const videoRes = await interviewApi.generateVideo(text, currentAvatarId.value)
      if (videoRes.data.video_url) {
        currentVideoUrl.value = videoRes.data.video_url
      }
    }
  } catch (e) {
    console.error('数字人内容生成失败:', e)
  }
}

function onVideoEnded() {
  currentVideoUrl.value = ''
}

async function loadStatus() {
  if (!session.value) return
  try {
    const res = await interviewApi.getSessionStatus(session.value.id)
    currentRound.value = res.data.current_round || 1
    maxRounds.value = res.data.max_rounds || 10
    duration.value = res.data.duration || 0
  } catch (e) {
    console.error('获取状态失败:', e)
  }
}

function startDurationTimer() {
  stopDurationTimer()
  durationTimer = setInterval(() => {
    duration.value++
  }, 1000)
}

function stopDurationTimer() {
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

async function sendAnswer() {
  const answer = userInput.value.trim()
  if (!answer || aiTyping.value) return

  userInput.value = ''
  aiTyping.value = true
  currentMessage.value = '让我思考一下...'

  // 停止当前音频
  stopAudio()

  try {
    const res = await interviewApi.submitAnswer(session.value.id, answer)
    aiTyping.value = false
    await loadMessages()
    await loadStatus()

    if (res.data.is_end) {
      stopDurationTimer()
      // 面试结束，加载报告
      await loadReport()
    }
  } catch (e) {
    console.error('发送回答失败:', e)
    aiTyping.value = false
    alert('发送失败，请重试')
  }
}

async function loadReport() {
  if (!session.value) return
  try {
    const res = await interviewApi.getReport(session.value.id)
    report.value = {
      ...res.data,
      strengths: res.data.strengths || [],
      weaknesses: res.data.weaknesses || [],
      detailed_feedback: res.data.detailed_feedback || {},
    }
    phase.value = 'report'
  } catch (e) {
    console.error('获取报告失败:', e)
    phase.value = 'report'
  }
}

async function endInterview() {
  showEndConfirm.value = false
  if (!session.value) return
  stopDurationTimer()

  try {
    await interviewApi.endInterview(session.value.id)
    await loadReport()
  } catch (e) {
    console.error('结束面试失败:', e)
  }
}

function resetInterview() {
  phase.value = 'prepare'
  session.value = null
  messages.value = []
  userInput.value = ''
  report.value = {}
  form.value = { position: '', resumeFile: null }
  if (fileInput.value) fileInput.value.value = ''
  stopDurationTimer()
  duration.value = 0
  currentRound.value = 1
  currentVideoUrl.value = ''
  currentAudioUrl.value = ''
  currentMessage.value = ''
  if (audioPlayer) {
    audioPlayer.pause()
    audioPlayer = null
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.app { min-height: 100vh; }

/* 准备阶段 */
.prepare-phase {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}
.prepare-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}
.prepare-card h1 { font-size: 28px; color: #1a1a2e; margin-bottom: 8px; }
.subtitle { color: #666; margin-bottom: 32px; }

.form-item { margin-bottom: 20px; }
.form-item label { display: block; font-weight: 500; margin-bottom: 8px; color: #333; }
.form-item select,
.form-item textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}
.form-item select:focus,
.form-item textarea:focus { outline: none; border-color: #4f46e5; }
.form-item textarea { resize: vertical; }

/* 上传区域 */
.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
}
.upload-area:hover { border-color: #4f46e5; }
.upload-placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #666; }
.upload-icon { font-size: 32px; }
.upload-hint { font-size: 12px; color: #999; }
.file-info { display: flex; align-items: center; justify-content: center; gap: 8px; }
.file-icon { font-size: 24px; }
.file-name { font-weight: 500; color: #333; }
.btn-remove { background: #ef4444; color: #fff; border: none; width: 20px; height: 20px; border-radius: 50%; cursor: pointer; font-size: 14px; line-height: 1; }

/* 按钮 */
.btn-primary {
  width: 100%;
  padding: 14px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover:not(:disabled) { background: #4338ca; }
.btn-primary:disabled { background: #a5a5a5; cursor: not-allowed; }
.btn-secondary { background: #e5e7eb; color: #333; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-text { background: none; border: none; color: #666; cursor: pointer; }

/* 面试阶段 */
.interview-phase {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.position-tag { background: #eef2ff; color: #4f46e5; padding: 4px 12px; border-radius: 16px; font-size: 14px; }
.status { color: #22c55e; font-size: 14px; }
.round-info { color: #666; font-size: 14px; }
.duration { color: #666; font-size: 14px; }

/* 数字人 */
.avatar-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}
.avatar-box { text-align: center; }
.avatar-display {
  width: 120px;
  height: 120px;
  margin: 0 auto 16px;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
}
.avatar-circle {
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-emoji { font-size: 48px; }
.avatar-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.audio-wave {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 3px;
  align-items: flex-end;
  height: 20px;
}
.audio-wave span {
  width: 3px;
  background: #fff;
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}
.audio-wave span:nth-child(1) { height: 8px; animation-delay: 0s; }
.audio-wave span:nth-child(2) { height: 12px; animation-delay: 0.1s; }
.audio-wave span:nth-child(3) { height: 16px; animation-delay: 0.2s; }
.audio-wave span:nth-child(4) { height: 12px; animation-delay: 0.3s; }
.audio-wave span:nth-child(5) { height: 8px; animation-delay: 0.4s; }
@keyframes wave {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1); }
}
.avatar-speak {
  color: #fff;
  font-size: 14px;
  max-width: 300px;
  margin: 0 auto;
  min-height: 40px;
}

/* 对话区 */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  background: #fff;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.message.interviewer { flex-direction: row; }
.message.interviewee { flex-direction: row-reverse; }
.message-avatar { width: 40px; height: 40px; background: #f3f4f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.message-content { max-width: 70%; }
.message-text { background: #f3f4f6; padding: 12px 16px; border-radius: 12px; line-height: 1.6; }
.message.interviewee .message-text { background: #4f46e5; color: #fff; }
.message-time { font-size: 12px; color: #999; margin-top: 4px; }

/* 输入区 */
.input-area {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #eee;
}
.input-area textarea { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; resize: none; font-size: 14px; }
.input-area textarea:focus { outline: none; border-color: #4f46e5; }
.btn-send {
  padding: 12px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.btn-send:disabled { background: #a5a5a5; cursor: not-allowed; }

/* 打字动画 */
.typing { display: flex; gap: 4px; padding: 12px 16px; }
.typing span {
  width: 8px; height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* 报告阶段 */
.report-phase {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
  min-height: 100vh;
}
.report-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}
.report-card h2 { font-size: 24px; color: #1a1a2e; margin-bottom: 8px; }
.score-section { text-align: center; margin: 32px 0; }
.score-circle {
  width: 140px; height: 140px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  color: #fff;
}
.score-num { font-size: 48px; font-weight: bold; }
.score-max { font-size: 16px; opacity: 0.8; }
.report-section { margin-bottom: 24px; }
.report-section h3 { font-size: 16px; color: #333; margin-bottom: 12px; }
.report-section ul { list-style: none; }
.report-section li { padding: 8px 0; border-bottom: 1px solid #f0f0f0; color: #555; }
.report-section ul.weakness li { color: #e55; }
.dimensions { display: flex; flex-direction: column; gap: 12px; }
.dimension-item { display: flex; align-items: center; gap: 12px; }
.dim-name { width: 80px; font-size: 14px; color: #666; }
.dim-bar { flex: 1; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
.dim-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 4px; transition: width 0.5s; }
.dim-score { width: 30px; text-align: right; font-weight: 500; }

/* 停止音频按钮 */
.btn-stop-audio {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.6);
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 12px;
  cursor: pointer;
  z-index: 10;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  width: 90%;
  max-width: 400px;
  text-align: center;
}
.modal h3 { font-size: 18px; margin-bottom: 8px; }
.modal p { color: #666; margin-bottom: 24px; }
.modal-btns { display: flex; gap: 12px; }
.modal-btns button { flex: 1; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
</style>
