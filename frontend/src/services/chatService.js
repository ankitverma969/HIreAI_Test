import apiClient from '../api/client';

export class ChatService {
  static async ask(question, sessionId = 'default') {
    return apiClient.post('/chat', {
      question,
      session_id: sessionId,
    });
  }

  static async getHistory(sessionId = 'default') {
    return apiClient.get('/chat/history', {
      params: { session_id: sessionId },
    });
  }

  static async clearHistory(sessionId = 'default') {
    return apiClient.delete('/chat/history', {
      params: { session_id: sessionId },
    });
  }
}

export default ChatService;
