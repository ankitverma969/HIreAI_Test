import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNotifications } from '../context/NotificationContext';
import styles from './FileUploader.module.css';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt']
};

const formatSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const FileUploader = ({ selectedFile, onFileSelect, onFileRemove, label = 'Job Description' }) => {
  const { showError } = useNotifications();

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      const reject = rejectedFiles[0];
      if (reject.file.size > MAX_FILE_SIZE) {
        showError('File exceeds the maximum size limit of 10MB.');
      } else {
        showError('Unsupported file type. Please upload a PDF, DOCX, or TXT file.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect, showError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
    accept: ACCEPTED_TYPES
  });

  return (
    <div>
      {!selectedFile ? (
        <div 
          {...getRootProps()} 
          className={`${styles.dropzone} ${isDragActive ? styles.active : ''}`}
        >
          <input {...getInputProps()} />
          <div className={styles.icon}>📄</div>
          <p className={styles.textMain}>Drag & drop your {label} here</p>
          <p className={styles.textSub}>Supports PDF, DOCX, or TXT (Max 10MB)</p>
        </div>
      ) : (
        <div className={styles.fileList}>
          <div className={styles.fileItem}>
            <div className={styles.fileInfo}>
              <span className={styles.fileIcon}>📄</span>
              <span className={styles.fileName}>{selectedFile.name}</span>
              <span className={styles.fileSize}>{formatSize(selectedFile.size)}</span>
            </div>
            <button 
              className={styles.removeBtn} 
              onClick={onFileRemove} 
              type="button"
              aria-label="Remove File"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export const MultiFileUploader = ({ selectedFiles = [], onFilesSelect, onFileRemove }) => {
  const { showError } = useNotifications();

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // 1. Handle error cases
    if (rejectedFiles.length > 0) {
      const oversized = rejectedFiles.some(r => r.file.size > MAX_FILE_SIZE);
      if (oversized) {
        showError('One or more files exceed the 10MB limit.');
      } else {
        showError('Contains unsupported file types. Please select PDF, DOCX, or TXT files only.');
      }
    }

    // 2. Process valid files
    const validFiles = acceptedFiles.filter((file) => {
      // Check for duplicates in current list
      const isDuplicate = selectedFiles.some(
        (sf) => sf.name === file.name && sf.size === file.size
      );
      if (isDuplicate) {
        showError(`File "${file.name}" is already uploaded.`);
        return false;
      }
      return true;
    });

    if (validFiles.length > 0) {
      onFilesSelect(validFiles);
    }
  }, [selectedFiles, onFilesSelect, showError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: MAX_FILE_SIZE,
    accept: ACCEPTED_TYPES
  });

  return (
    <div>
      <div 
        {...getRootProps()} 
        className={`${styles.dropzone} ${isDragActive ? styles.active : ''}`}
      >
        <input {...getInputProps()} />
        <div className={styles.icon}>📁</div>
        <p className={styles.textMain}>Drag & drop multiple Candidate Resumes here</p>
        <p className={styles.textSub}>Upload up to 10+ resumes in PDF, DOCX, or TXT format (Max 10MB each)</p>
      </div>

      {selectedFiles.length > 0 && (
        <div className={styles.fileList}>
          {selectedFiles.map((file, index) => (
            <div key={`${file.name}-${index}`} className={styles.fileItem}>
              <div className={styles.fileInfo}>
                <span className={styles.fileIcon}>👤</span>
                <span className={styles.fileName}>{file.name}</span>
                <span className={styles.fileSize}>{formatSize(file.size)}</span>
              </div>
              <button 
                className={styles.removeBtn} 
                onClick={() => onFileRemove(index)} 
                type="button"
                aria-label={`Remove resume ${file.name}`}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default FileUploader;
