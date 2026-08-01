import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidates } from '../context/CandidateContext';
import { useAnalysis } from '../context/AnalysisContext';
import { Card, Button } from '../components';
import styles from './Dashboard.module.css';

export const Dashboard = () => {
  const navigate = useNavigate();
  const { rankings, fetchResults, jobTitle } = useCandidates();
  const { screeningStatus } = useAnalysis();

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // Calculate metrics
  const totalCandidates = rankings.length;
  const avgScore = totalCandidates
    ? Math.round(rankings.reduce((acc, curr) => acc + curr.score.overall_score, 0) / totalCandidates)
    : 0;
  const maxScore = totalCandidates
    ? Math.max(...rankings.map((r) => r.score.overall_score))
    : 0;
  const strongHireCount = rankings.filter(
    (r) => (r.score.reasoning || '').toLowerCase().includes('strong hire') || r.score.overall_score >= 90
  ).length;

  return (
    <div>
      {/* Metrics Row */}
      <div className={styles.grid}>
        <div className={styles.metricCard}>
          <div className={styles.iconWrapper}>👤</div>
          <div className={styles.metricInfo}>
            <span className={styles.metricValue}>{totalCandidates}</span>
            <span className={styles.metricLabel}>Total Candidates</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.iconWrapper}>📈</div>
          <div className={styles.metricInfo}>
            <span className={styles.metricValue}>{avgScore}%</span>
            <span className={styles.metricLabel}>Average Match</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.iconWrapper}>🏆</div>
          <div className={styles.metricInfo}>
            <span className={styles.metricValue}>{maxScore}%</span>
            <span className={styles.metricLabel}>Highest Match</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.iconWrapper}>🔥</div>
          <div className={styles.metricInfo}>
            <span className={styles.metricValue}>{strongHireCount}</span>
            <span className={styles.metricLabel}>Strong Hires</span>
          </div>
        </div>
      </div>

      {/* Target JD status card if loaded */}
      {jobTitle && (
        <Card title="Current Target Job Description" style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>{jobTitle}</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Pipeline run status: <span style={{ color: 'var(--success)', fontWeight: 600 }}>Active</span>
              </p>
            </div>
            <Button onClick={() => navigate('/results')} variant="secondary">
              View Detailed Results
            </Button>
          </div>
        </Card>
      )}

      {/* Shortcuts Actions grid */}
      <div className={styles.actionsSection}>
        <h2 className={styles.sectionTitle}>ATS Actions Panel</h2>
        <div className={styles.actionGrid}>
          <Card className={styles.actionCard} title="1. Setup AI Screening Pipeline">
            <p className={styles.actionDesc}>
              Upload a target job description and drag-and-drop resumes (PDF, DOCX, TXT) to parse technical credentials.
            </p>
            <Button onClick={() => navigate('/upload')} style={{ marginTop: 'auto' }}>
              Initiate Screening
            </Button>
          </Card>

          <Card className={styles.actionCard} title="2. View Candidate Ranks">
            <p className={styles.actionDesc}>
              Review deterministic overall scores, skill overlap percentages, academic matches, and custom AI recommendations.
            </p>
            <Button onClick={() => navigate('/results')} variant="secondary" style={{ marginTop: 'auto' }}>
              Browse Rankings
            </Button>
          </Card>

          <Card className={styles.actionCard} title="3. Analytics & Score Spread">
            <p className={styles.actionDesc}>
              Explore distribution graphs, top matching skills, experience histograms, and download complete reports.
            </p>
            <Button onClick={() => navigate('/analytics')} variant="secondary" style={{ marginTop: 'auto' }}>
              Open Analytics
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
