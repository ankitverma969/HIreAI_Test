import apiClient from '../api/client';

export class ComparisonService {
  static async compare(candidateIds) {
    return apiClient.post('/compare', {
      candidate_ids: candidateIds,
    });
  }
}

export default ComparisonService;
