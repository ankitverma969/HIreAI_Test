import axios from 'axios';
import apiClient from '../api/client';

export class ExecutiveService {
  static async getAnalytics() {
    return apiClient.get('/analytics');
  }

  static async getExecutiveSummary() {
    return apiClient.get('/executive-summary');
  }

  static async getInsights() {
    return apiClient.get('/insights');
  }

  static async getHiringReport() {
    return apiClient.get('/hiring-report');
  }

  static async downloadReport(format) {
    const filenames = {
      pdf: 'executive_hiring_report.pdf',
      markdown: 'executive_hiring_report.md',
      csv: 'hiring_analytics.csv',
      json: 'hiring_analytics.json',
    };
    const response = await axios.get('http://localhost:8000/hiring-report', {
      params: { format, download: true },
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filenames[format] || 'executive_hiring_report');
    document.body.appendChild(link);
    link.click();
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    window.URL.revokeObjectURL(url);
  }
}

export default ExecutiveService;
