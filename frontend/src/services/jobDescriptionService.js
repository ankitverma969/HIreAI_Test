import apiClient from '../api/client';

export class JobDescriptionService {
  static async upload(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/job-description/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}
export default JobDescriptionService;
