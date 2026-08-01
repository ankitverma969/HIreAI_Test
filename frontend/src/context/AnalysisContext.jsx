import React, { createContext, useContext, useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { AnalysisService } from '../services/analysisService';
import { useNotifications } from './NotificationContext';

const AnalysisContext = createContext();

export const AnalysisProvider = ({ children }) => {
  const { showError, showSuccess } = useNotifications();

  // Upload States
  const [jdFile, setJdFile] = useState(null);
  const [jdPath, setJdPath] = useState('');
  const [resumeFiles, setResumeFiles] = useState([]);
  const [resumesPaths, setResumesPaths] = useState([]);

  // Screening status
  const [screeningStatus, setScreeningStatus] = useState('idle'); // idle, in_progress, success, error
  const [screeningStage, setScreeningStage] = useState('');
  const [screeningMessage, setScreeningMessage] = useState('');
  const [reportId, setReportId] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Timer effect
  useEffect(() => {
    let interval = null;
    if (screeningStatus === 'in_progress') {
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    } else if (screeningStatus === 'idle') {
      setElapsedTime(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [screeningStatus]);

  // Handle WebSocket progress updates
  const handleWebSocketMessage = (msg) => {
    if (msg.type === 'progress') {
      setScreeningStatus('in_progress');
      setScreeningStage(msg.stage);
      setScreeningMessage(msg.message);
    } else if (msg.type === 'completed') {
      setScreeningStatus('success');
      setScreeningStage('completed');
      setScreeningMessage(msg.message);
      setReportId(msg.report_id);
      showSuccess('AI screening completed successfully!');
    } else if (msg.type === 'error') {
      setScreeningStatus('error');
      setScreeningStage('failed');
      setScreeningMessage(msg.message);
      showError(msg.message || 'Screening pipeline failed.');
    }
  };

  // Derive WebSocket URL dynamically from the stored server URL
  const getWsUrl = () => {
    const raw = localStorage.getItem('serverUrl');
    // Prefer an explicit serverUrl stored in localStorage, otherwise fall back to the current origin with port 8000
    let serverUrl = raw && raw.trim().length > 0 ? raw.trim() : `${window.location.protocol}//${window.location.hostname}:8000`;

    // If the stored value already uses ws/wss, ensure it ends with /ws
    if (/^wss?:\/\//i.test(serverUrl)) {
      return serverUrl.replace(/\/$/, '') + '/ws';
    }

    // If protocol is http or https, convert to ws or wss depending on page protocol
    if (/^https?:\/\//i.test(serverUrl)) {
      const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws';
      return serverUrl.replace(/^https?:/i, wsProto + ':') .replace(/\/$/, '') + '/ws';
    }

    // Otherwise assume hostname (with optional port) and build ws URL
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${serverUrl.replace(/\/$/, '')}/ws`;
  };

  // Instantiate live WebSocket listener
  const { status: wsStatus } = useWebSocket(getWsUrl(), handleWebSocketMessage);


  const startScreening = async () => {
    if (!jdPath) {
      showError('Please upload a job description first.');
      return false;
    }
    if (resumesPaths.length === 0) {
      showError('Please upload at least one candidate resume.');
      return false;
    }

    setScreeningStatus('in_progress');
    setScreeningStage('validate_input');
    setScreeningMessage('Initiating analysis workflow...');
    setElapsedTime(0);

    try {
      await AnalysisService.screen(jdPath, resumesPaths);
      return true;
    } catch (e) {
      setScreeningStatus('error');
      setScreeningStage('failed');
      setScreeningMessage(e.message || 'Failed to start screening pipeline.');
      showError(e.message || 'An error occurred during workflow initiation.');
      return false;
    }
  };

  const resetScreening = () => {
    setScreeningStatus('idle');
    setScreeningStage('');
    setScreeningMessage('');
    setElapsedTime(0);
    setReportId(null);
  };

  const clearUploads = () => {
    setJdFile(null);
    setJdPath('');
    setResumeFiles([]);
    setResumesPaths([]);
    resetScreening();
  };

  return (
    <AnalysisContext.Provider
      value={{
        jdFile,
        setJdFile,
        jdPath,
        setJdPath,
        resumeFiles,
        setResumeFiles,
        resumesPaths,
        setResumesPaths,
        screeningStatus,
        screeningStage,
        screeningMessage,
        reportId,
        elapsedTime,
        wsStatus,
        startScreening,
        resetScreening,
        clearUploads,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};
export default AnalysisContext;
