import { useState } from 'react';
import { useAnalysis } from '../context/AnalysisContext';
import { useNotifications } from '../context/NotificationContext';
import { JobDescriptionService } from '../services/jobDescriptionService';
import { ResumeService } from '../services/resumeService';

export const useUpload = () => {
  const { setJdFile, setJdPath, setResumeFiles, setResumesPaths, resumeFiles, resumesPaths } = useAnalysis();
  const { showSuccess, showError } = useNotifications();
  const [isUploadingJd, setIsUploadingJd] = useState(false);
  const [isUploadingResumes, setIsUploadingResumes] = useState(false);

  const uploadJD = async (file) => {
    setIsUploadingJd(true);
    try {
      const response = await JobDescriptionService.upload(file);
      // Response structure: { success: true, message: "...", data: { filename, saved_path, size_bytes } }
      if (response && response.data) {
        setJdFile(file);
        setJdPath(response.data.saved_path);
        showSuccess('Job Description uploaded and validated successfully!');
        return response.data.saved_path;
      }
    } catch (e) {
      showError(e.message || 'Failed to upload Job Description.');
    } finally {
      setIsUploadingJd(false);
    }
    return null;
  };

  const uploadResumes = async (files) => {
    setIsUploadingResumes(true);
    try {
      const response = await ResumeService.upload(files);
      // Response structure: { success: true, data: [ { filename, saved_path, size_bytes }, ... ] }
      if (response && response.data) {
        const newPaths = response.data.map((r) => r.saved_path);
        setResumeFiles((prev) => [...prev, ...files]);
        setResumesPaths((prev) => [...prev, ...newPaths]);
        showSuccess(`Successfully uploaded ${files.length} resume(s)!`);
        return newPaths;
      }
    } catch (e) {
      showError(e.message || 'Failed to upload resumes.');
    } finally {
      setIsUploadingResumes(false);
    }
    return null;
  };

  const removeResumeFile = (index) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
    setResumesPaths((prev) => prev.filter((_, i) => i !== index));
    showSuccess('Resume removed.');
  };

  return {
    uploadJD,
    uploadResumes,
    removeResumeFile,
    isUploading: isUploadingJd || isUploadingResumes,
    isUploadingJd,
    isUploadingResumes,
  };
};

export default useUpload;
