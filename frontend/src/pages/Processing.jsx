import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '../context/AnalysisContext';
import { ProgressBar, Button, Card } from '../components';
import styles from './Processing.module.css';

export const Processing = () => {
  const navigate = useNavigate();
  const {
    screeningStatus,
    screeningStage,
    screeningMessage,
    elapsedTime,
    resetScreening,
  } = useAnalysis();

  const stages = useMemo(() => [
    { key: 'validate_input', label: 'Uploading & Validating Inputs', pct: 10 },
    { key: 'parse_jd', label: 'Parsing Job Description', pct: 20 },
    { key: 'load_resumes', label: 'Parsing Candidate Resumes', pct: 35 },
    { key: 'embedding_generation', label: 'Generating Dense Embeddings', pct: 55 },
    { key: 'similarity_calculation', label: 'Calculating Semantic Similarity', pct: 65 },
    { key: 'score_generation', label: 'Rule-Based Weighted Scoring', pct: 75 },
    { key: 'reasoning_generation', label: 'Generating AI Qualitative Analysis', pct: 85 },
    { key: 'recommendation', label: 'Compiling Hiring Decision Recommendation', pct: 90 },
    { key: 'ranking', label: 'Deterministic Candidate Ranking', pct: 95 },
    { key: 'report_generation', label: 'ATS Reports Compilation', pct: 99 },
    { key: 'completed', label: 'Screening Completed', pct: 100 },
  ], []);

  // Find index of current stage
  const currentStageIndex = useMemo(() => {
    return stages.findIndex((s) => s.key === screeningStage);
  }, [stages, screeningStage]);

  // Calculate overall percentage completed
  const currentPercentage = useMemo(() => {
    if (screeningStatus === 'success') return 100;
    if (screeningStatus === 'idle') return 0;
    if (currentStageIndex === -1) return 5;
    return stages[currentStageIndex].pct;
  }, [stages, screeningStatus, currentStageIndex]);

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const getStageStatus = (index) => {
    if (screeningStatus === 'success') return 'completed';
    if (screeningStatus === 'error') {
      if (index === currentStageIndex) return 'failed';
      if (index < currentStageIndex) return 'completed';
      return 'pending';
    }
    if (index < currentStageIndex) return 'completed';
    if (index === currentStageIndex) return 'active';
    return 'pending';
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Live Ingestion Monitor</h2>
        <div className={styles.timer}>{formatTime(elapsedTime)}</div>
      </div>

      <p className={styles.statusMessage}>
        {screeningMessage || 'Initializing screening execution blocks...'}
      </p>

      <ProgressBar value={currentPercentage} label="Overall Screening Progress" />

      {/* Live Stage List */}
      <div className={styles.stageList}>
        {stages.map((stage, idx) => {
          const status = getStageStatus(idx);
          let itemClass = styles.stageItem;
          let indicator = null;

          if (status === 'active') {
            itemClass += ` ${styles.stageActive}`;
            indicator = <div className={styles.spinnerIndicator} />;
          } else if (status === 'completed') {
            itemClass += ` ${styles.stageCompleted}`;
            indicator = <span className={`${styles.stageIndicator} ${styles.successIndicator}`}>✓ Done</span>;
          } else if (status === 'failed') {
            itemClass += ` ${styles.stageActive}`;
            indicator = <span style={{ color: 'var(--danger)', fontWeight: 'bold' }}>✕ Failed</span>;
          } else {
            itemClass += ` ${styles.stagePending}`;
            indicator = <span style={{ color: 'var(--text-muted)' }}>Waiting...</span>;
          }

          return (
            <div key={stage.key} className={itemClass}>
              <div className={styles.stageLeft}>
                <span className={styles.stageIcon}>
                  {status === 'completed' ? '🟢' : status === 'failed' ? '🔴' : '⚫'}
                </span>
                <span className={styles.stageLabel}>{stage.label}</span>
              </div>
              {indicator}
            </div>
          );
        })}
      </div>

      {/* Control Actions Footer */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px', marginTop: '32px', borderTop: '1px solid var(--border-color)', paddingTop: '24px' }}>
        {screeningStatus === 'error' && (
          <Button variant="secondary" onClick={() => navigate('/upload')}>
            Back to Upload
          </Button>
        )}
        {screeningStatus === 'success' && (
          <Button onClick={() => navigate('/results')} icon="🏆">
            View Ranked Candidates
          </Button>
        )}
      </div>
    </div>
  );
};

export default Processing;
