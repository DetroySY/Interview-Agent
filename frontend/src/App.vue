<template>
  <div class="page">
    <!-- ========== 准备阶段 ========== -->
    <section v-if="phase === 'prepare'" class="prepare">
      <div class="card">
        <h1 class="title">AI 模拟面试</h1>
        <p class="subtitle">智能面试官 · 多轮对话 · 反馈报告</p>

        <div class="field">
          <label>面试岗位</label>
          <select v-model="form.position">
            <option value="" disabled>请选择岗位</option>
            <option v-for="p in positions" :key="p" :value="p">{{ p }}</option>
          </select>
        </div>

        <div class="field">
          <label>简历文件</label>
          <label class="uploader" :class="{ active: form.resumeFile }">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              hidden
              @change="handleFile"
            />
            <template v-if="form.resumeFile">
              <span class="file-name">{{ form.resumeFile.name }}</span>
              <button class="x" @click.prevent="removeFile">×</button>
            </template>
            <template v-else>
              <span>点击上传 · PDF / Word / TXT</span>
            </template>
          </label>
        </div>

        <button
          class="btn-primary"
          :disabled="!canStart || starting"
          @click="start"
        >
          {{ starting ? '准备中…' : '开始面试' }}
        </button>
      </div>
    </section>

    <!-- ========== 面试阶段 ========== -->
    <section v-else-if="phase === 'interview'" class="interview">
      <header class="topbar">
        <span class="tag">{{ session.position }}</span>
        <span class="round">第 {{ currentRound }} / {{ maxRounds }} 轮</span>
        <span class="spacer" />
        <button class="btn-ghost" @click="confirmEnd = true">结束面试</button>
      </header>

      <div class="messages" ref="msgBox">
        <div
          v-for="m in messages"
          :key="m.id"
          :class="['msg', m.role]"
        >
          <div class="bubble">{{ m.content }}</div>
          <div class="time">{{ formatTime(m.timestamp) }}</div>
        </div>
        <div v-if="aiTyping" class="msg interviewer">
          <div class="bubble thinking">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div class="composer">
        <textarea
          v-model="userInput"
          placeholder="输入你的回答，回车发送，Shift+Enter 换行"
          :disabled="aiTyping"
          @keydown.enter.exact.prevent="send"
        />
        <button class="btn-primary" :disabled="!canSend" @click="send">
          发送
        </button>
      </div>
    </section>

    <!-- ========== 报告阶段 ========== -->
    <section v-else class="report">
      <div class="card">
        <h2 class="title">面试报告</h2>
        <p class="subtitle">本次面试综合评估</p>

        <div class="score-block">
          <div class="score-circle">
            <span class="score-num">{{ report.overall_score || 0 }}</span>
            <span class="score-max">/ 10</span>
          </div>
        </div>

        <div class="section">
          <h3>综合评价</h3>
          <ul>
            <li v-for="(s, i) in report.strengths" :key="'s' + i" class="ok">
              {{ s }}
            </li>
          </ul>
          <ul>
            <li v-for="(w, i) in report.weaknesses" :key="'w' + i" class="bad">
              {{ w }}
            </li>
          </ul>
        </div>

        <div class="section">
          <h3>维度评分</h3>
          <div
            v-for="(score, key) in report.detailed_feedback"
            :key="key"
            class="dim"
          >
            <span class="dim-name">{{ key }}</span>
            <div class="dim-bar">
              <div class="dim-fill" :style="{ width: score * 10 + '%' }" />
            </div>
            <span class="dim-score">{{ score }}</span>
          </div>
        </div>

        <button class="btn-primary" @click="reset">再来一次</button>
      </div>
    </section>

    <!-- ========== 结束确认弹窗 ========== -->
    <div v-if="confirmEnd" class="modal" @click.self="confirmEnd = false">
      <div class="modal-card">
        <h3>结束本次面试？</h3>
        <p>结束后将生成反馈报告，无法继续作答。</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="confirmEnd = false">继续</button>
          <button class="btn-danger" @click="end">确认结束</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { interviewApi } from './api.js'

const positions = ['前端开发', '后端开发', '全栈开发', '产品经理', '数据分析师', 'AI 工程师']

// ===== 状态 =====
const phase = ref('prepare') // prepare | interview | report
const form = ref({ position: '', resumeFile: null })
const starting = ref(false)
const session = ref(null)
const messages = ref([])
const userInput = ref('')
const aiTyping = ref(false)
const report = ref({})
const confirmEnd = ref(false)
const msgBox = ref(null)

const currentRound = ref(1)
const maxRounds = ref(10)

const canStart = computed(() => form.value.position && form.value.resumeFile)
const canSend = computed(() => userInput.value.trim() && !aiTyping.value)

// ===== 准备阶段 =====
function handleFile(e) {
  const file = e.target.files[0]
  if (file) form.value.resumeFile = file
}

function removeFile() {
  form.value.resumeFile = null
}

async function start() {
  if (!canStart.value || starting.value) return
  starting.value = true
  try {
    const fd = new FormData()
    fd.append('user_id', 'user_' + Date.now())
    fd.append('position', form.value.position)
    fd.append('resume_file', form.value.resumeFile)
    const { data } = await interviewApi.createSession(fd)
    session.value = data
    await interviewApi.startInterview(data.id)
    await loadMessages()
    await loadStatus()
    phase.value = 'interview'
  } catch (err) {
    console.error(err)
    alert('启动失败：' + (err.response?.data?.detail || err.message))
  } finally {
    starting.value = false
  }
}

// ===== 面试阶段 =====
async function loadMessages() {
  if (!session.value) return
  const { data } = await interviewApi.getMessages(session.value.id)
  messages.value = data
  scrollBottom()
}

async function loadStatus() {
  if (!session.value) return
  const { data } = await interviewApi.getSessionStatus(session.value.id)
  currentRound.value = data.current_round || 1
  maxRounds.value = data.max_rounds || 10
}

async function send() {
  const text = userInput.value.trim()
  if (!text || aiTyping.value) return
  userInput.value = ''
  aiTyping.value = true
  try {
    const { data } = await interviewApi.submitAnswer(session.value.id, text)
    await loadMessages()
    await loadStatus()
    if (data.is_end) await loadReport()
  } catch (err) {
    console.error(err)
    alert('发送失败，请重试')
  } finally {
    aiTyping.value = false
  }
}

function scrollBottom() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

// ===== 结束 / 报告 =====
async function end() {
  confirmEnd.value = false
  if (!session.value) return
  try {
    await interviewApi.endInterview(session.value.id)
    await loadReport()
  } catch (err) {
    console.error(err)
  }
}

async function loadReport() {
  if (!session.value) return
  const { data } = await interviewApi.getReport(session.value.id)
  report.value = {
    overall_score: data.overall_score,
    strengths: data.strengths || [],
    weaknesses: data.weaknesses || [],
    detailed_feedback: data.detailed_feedback || {},
  }
  phase.value = 'report'
}

function reset() {
  phase.value = 'prepare'
  session.value = null
  messages.value = []
  userInput.value = ''
  report.value = {}
  form.value = { position: '', resumeFile: null }
  currentRound.value = 1
}

// ===== 工具 =====
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
* { box-sizing: border-box; }
.page {
  min-height: 100vh;
  background: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  color: #0f172a;
  font-size: 14px;
}

/* ===== 共用卡片 ===== */
.card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}
.title { font-size: 22px; margin: 0 0 6px; }
.subtitle { color: #64748b; margin: 0 0 28px; font-size: 14px; }

.field { margin-bottom: 20px; }
.field label {
  display: block;
  font-weight: 500;
  margin-bottom: 8px;
  color: #334155;
}
select, textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  transition: border-color 0.15s;
  font-family: inherit;
}
select:focus, textarea:focus {
  outline: none;
  border-color: #2563eb;
}

/* ===== 上传 ===== */
.uploader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s;
}
.uploader:hover { border-color: #2563eb; color: #2563eb; }
.uploader.active { border-style: solid; color: #0f172a; }
.file-name { font-weight: 500; }
.x {
  border: none;
  background: #f1f5f9;
  color: #64748b;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}

/* ===== 按钮 ===== */
.btn-primary {
  width: 100%;
  padding: 12px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-primary:disabled { background: #cbd5e1; cursor: not-allowed; }

.btn-ghost {
  background: transparent;
  border: 1px solid #cbd5e1;
  color: #475569;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-family: inherit;
}
.btn-ghost:hover { background: #f1f5f9; }

.btn-danger {
  background: #dc2626;
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-family: inherit;
}
.btn-danger:hover { background: #b91c1c; }

/* ===== 准备阶段 ===== */
.prepare {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

/* ===== 面试阶段 ===== */
.interview {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
}
.tag {
  background: #eff6ff;
  color: #2563eb;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}
.round { color: #64748b; font-size: 13px; }
.spacer { flex: 1; }

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  background: #f8fafc;
}
.msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
  max-width: 75%;
}
.msg.interviewer { align-items: flex-start; }
.msg.interviewee { align-items: flex-end; margin-left: auto; }

.bubble {
  padding: 10px 14px;
  border-radius: 10px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}
.msg.interviewer .bubble {
  background: #fff;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  border-top-left-radius: 2px;
}
.msg.interviewee .bubble {
  background: #2563eb;
  color: #fff;
  border-top-right-radius: 2px;
}
.time { font-size: 11px; color: #94a3b8; margin-top: 4px; padding: 0 4px; }

/* 思考动画 */
.thinking { display: flex; gap: 4px; padding: 14px 16px; }
.thinking span {
  width: 6px; height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  animation: dot 1.4s infinite;
}
.thinking span:nth-child(2) { animation-delay: 0.2s; }
.thinking span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* 输入区 */
.composer {
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background: #fff;
}
.composer textarea {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  padding: 10px 12px;
}
.composer .btn-primary { width: auto; padding: 10px 24px; }

/* ===== 报告阶段 ===== */
.report {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.report .card { max-width: 560px; }
.score-block {
  display: flex;
  justify-content: center;
  margin: 24px 0 32px;
}
.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: #2563eb;
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.score-num { font-size: 40px; font-weight: 600; line-height: 1; }
.score-max { font-size: 13px; opacity: 0.85; margin-top: 4px; }

.section { margin-bottom: 24px; }
.section h3 {
  font-size: 14px;
  color: #334155;
  margin: 0 0 12px;
  font-weight: 600;
}
.section ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.section li {
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.6;
}
.section li.ok { background: #f0fdf4; color: #166534; }
.section li.bad { background: #fef2f2; color: #991b1b; }

.dim {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.dim-name { width: 80px; font-size: 13px; color: #475569; }
.dim-bar {
  flex: 1;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}
.dim-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 3px;
  transition: width 0.5s;
}
.dim-score { width: 28px; text-align: right; font-weight: 600; }

/* ===== 弹窗 ===== */
.modal {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 24px;
}
.modal-card {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
  width: 100%;
  max-width: 360px;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15);
}
.modal-card h3 { margin: 0 0 8px; font-size: 16px; }
.modal-card p { color: #64748b; margin: 0 0 20px; font-size: 13px; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
</style>