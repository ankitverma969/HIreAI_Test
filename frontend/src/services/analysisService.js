import apiClient from '../api/client';

export class AnalysisService {
  /**
   * Kick off the AI screening pipeline.
   * Passes the user's saved model settings (from Settings page) to the
   * backend so the correct LLM model is used for this run.
   */
  static async screen(jdPath, resumesPaths) {
    const llmModel       = localStorage.getItem('llmModel')       || 'gemini-1.5-flash';
    const embeddingModel = localStorage.getItem('embeddingModel') || 'all-MiniLM-L6-v2';
    const temperature    = parseFloat(localStorage.getItem('temperature') || '0.0');
    const geminiApiBase   = localStorage.getItem('geminiApiBase') || '';

    return apiClient.post('/screen', {
      job_description_path: jdPath,
      resumes_paths: resumesPaths,
      // Runtime overrides — backend respects these if supported
      llm_model: llmModel,
      embedding_model: embeddingModel,
      temperature,
      gemini_api_base: geminiApiBase,
    });
  }
}

export default AnalysisService;
