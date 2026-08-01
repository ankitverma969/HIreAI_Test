import apiClient from '../api/client';

export class ResumeService {
  static async upload(files) {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    return apiClient.post('/resumes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}
export default ResumeService;
