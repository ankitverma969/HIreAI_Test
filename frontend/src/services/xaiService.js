import axios from 'axios';
import apiClient from '../api/client';

export class XAIService {
  static async getResults() {
    return apiClient.get('/results');
  }

  static async getCandidateExplanation(candidateId) {
    return apiClient.get(`/explain/${candidateId}`);
  }

  static async getAuditLog(params = {}) {
    return apiClient.get('/audit', { params });
  }

  static async downloadAuditCsv(params = {}) {
    const response = await axios.get('http://localhost:8000/audit', {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'decision_audit_log.csv');
    document.body.appendChild(link);
    link.click();
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    window.URL.revokeObjectURL(url);
  }

  static async getGraphExecution() {
    return apiClient.get('/graph/execution');
  }

  static async getGraphTimeline() {
    return apiClient.get('/graph/timeline');
  }

  static async getPromptHistory() {
    return apiClient.get('/prompt-history');
  }
}

export default XAIService;
