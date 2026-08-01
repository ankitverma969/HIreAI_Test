import axios from 'axios';

export class DownloadService {
  static async downloadCSV() {
    return this._download('/download/csv', 'resume_screening_report.csv');
  }

  static async downloadJSON() {
    return this._download('/download/json', 'resume_screening_report.json');
  }

  static async downloadReport() {
    return this._download('/download/report', 'resume_screening_report.md');
  }

  static async _download(endpoint, filename) {
    const response = await axios.get(`http://localhost:8000${endpoint}`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    window.URL.revokeObjectURL(url);
  }
}
export default DownloadService;
