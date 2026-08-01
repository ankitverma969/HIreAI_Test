import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { useUpload } from '../hooks/useUpload';
import { Button, FileUploader, MultiFileUploader } from '../components';
import styles from './Upload.module.css';

export const Upload = () => {
  const navigate = useNavigate();
  const { jdFile, resumeFiles, jdPath, resumesPaths, startScreening, clearUploads } = useAnalysis();
  const { uploadJD, uploadResumes, removeResumeFile, isUploading } = useUpload();

  const handleStartScreening = async () => {
    const success = await startScreening();
    if (success) {
      navigate('/processing');
    }
  };

  const isAnalyzeDisabled = !jdPath || resumesPaths.length === 0 || isUploading;

  return (
    <div>
      <div className={styles.container}>
        {/* Job Description Uploader Box */}
        <div className={styles.uploadBox}>
          <h2 className={styles.title}>1. Target Job Description</h2>
          <FileUploader
            selectedFile={jdFile}
            onFileSelect={uploadJD}
            onFileRemove={clearUploads}
            label="Job Description"
          />
        </div>

        {/* Resumes Uploader Box */}
        <div className={styles.uploadBox}>
          <h2 className={styles.title}>2. Resumes Ingestion</h2>
          <MultiFileUploader
            selectedFiles={resumeFiles}
            onFilesSelect={uploadResumes}
            onFileRemove={removeResumeFile}
          />
        </div>
      </div>

      {/* Control Buttons Footer Bar */}
      <div className={styles.bottomBar}>
        {(jdFile || resumeFiles.length > 0) && (
          <Button variant="secondary" onClick={clearUploads} disabled={isUploading}>
            Clear All
          </Button>
        )}
        <Button
          variant="primary"
          onClick={handleStartScreening}
          disabled={isAnalyzeDisabled}
          loading={isUploading}
          icon="🚀"
        >
          Start AI Resume Screening
        </Button>
      </div>
    </div>
  );
};

export default Upload;
