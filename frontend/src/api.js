import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 120000,
})

export const interviewApi = {
  // 创建会话
  createSession(data) {
    return api.post('/interview/sessions', data)
  },

  // 开始面试
  startInterview(sessionId) {
    return api.post(`/interview/sessions/${sessionId}/start`)
  },

  // 提交回答
  submitAnswer(sessionId, answer) {
    return api.post(`/interview/sessions/${sessionId}/answer`, null, {
      params: { answer }
    })
  },

  // 获取消息历史
  getMessages(sessionId) {
    return api.get(`/interview/sessions/${sessionId}/messages`)
  },

  // 获取报告
  getReport(sessionId) {
    return api.get(`/interview/sessions/${sessionId}/report`)
  },

  // 结束面试
  endInterview(sessionId) {
    return api.post(`/interview/sessions/${sessionId}/end`)
  },

  // 获取面试状态
  getSessionStatus(sessionId) {
    return api.get(`/interview/sessions/${sessionId}/status`)
  },

  // 获取历史会话列表
  getSessions(userId) {
    return api.get('/interview/sessions', { params: { user_id: userId } })
  },

  // 生成 TTS 音频
  generateAudio(text) {
    return api.get('/interview/audio/generate', { params: { text } })
  },

  // 生成数字人视频
  generateVideo(text, avatar = 'default') {
    return api.post('/interview/video/generate', null, { params: { text, avatar } })
  },
}

export default api
