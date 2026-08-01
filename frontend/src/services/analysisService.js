import apiClient from '../api/client';

export class AnalysisService {
  static async screen(jdPath, resumesPaths) {
    return apiClient.post('/screen', {
      job_description_path: jdPath,
      resumes_paths: resumesPaths,
    });
  }
}
export default AnalysisService;
