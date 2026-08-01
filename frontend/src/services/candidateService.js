import apiClient from '../api/client';

export class CandidateService {
  static async getResults() {
    return apiClient.get('/results');
  }

  static async getCandidate(id) {
    return apiClient.get(`/candidate/${id}`);
  }
}
export default CandidateService;
