import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidates } from '../context/CandidateContext';
import { useAnalysis } from '../context/AnalysisContext';
import { Card, Button } from '../components';
import styles from './Dashboard.module.css';

const MetricCard = ({ icon, value, label, delta, accentClass }) => (
  <div className={`${styles.metricCard} ${accentClass || ''}`}>
    <div className={styles.metricIcon}>{icon}</div>
    <div className={styles.metricBody}>
      <span className={styles.metricValue}>{value}</span>
      <span className={styles.metricLabel}>{label}</span>
      {delta && <span className={styles.metricDelta}>{delta}</span>}
    </div>
    <div className={styles.metricGlow} />
  </div>
);

const ActionCard = ({ icon, step, title, desc, cta, onClick, variant = 'secondary' }) => (
  <div className={styles.actionCard} onClick={onClick} role="button" tabIndex={0}
    onKeyDown={(e) => e.key === 'Enter' && onClick()}>
    <div className={styles.actionCardInner}>
      <div className={styles.actionStep}>{step}</div>
      <div className={styles.actionIcon}>{icon}</div>
      <h3 className={styles.actionTitle}>{title}</h3>
      <p className={styles.actionDesc}>{desc}</p>
      <Button variant={variant} onClick={onClick} style={{ marginTop: 'auto', alignSelf: 'flex-start' }}>
        {cta}
      </Button>
    </div>
    <div className={styles.actionCardGlow} />
  </div>
);

export const Dashboard = () => {
  const navigate = useNavigate();
  const { rankings, fetchResults, jobTitle } = useCandidates();
  const { screeningStatus, wsStatus } = useAnalysis();

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const totalCandidates = rankings.length;
  const avgScore = totalCandidates
    ? Math.round(rankings.reduce((acc, r) => acc + r.score.overall_score, 0) / totalCandidates)
    : 0;
  const maxScore = totalCandidates
    ? Math.max(...rankings.map((r) => r.score.overall_score))
    : 0;
  const strongHireCount = rankings.filter(
    (r) => (r.score.reasoning || '').toLowerCase().includes('strong hire') || r.score.overall_score >= 90
  ).length;

  const isActive = screeningStatus === 'in_progress';

  return (
    <div className={styles.page}>
      {/* ── Hero Banner ─────────────────────────────────────── */}
      <div className={styles.hero}>
        <div className={styles.heroText}>
          <div className={styles.heroBadge}>
            <span className={`${styles.heroStatus} ${isActive ? styles.heroStatusActive : ''}`} />
            {isActive ? 'Pipeline Running' : 'System Ready'}
          </div>
          <h1 className={styles.heroTitle}>
            AI-Powered<br />
            <span className={styles.heroGradient}>Talent Acquisition</span>
          </h1>
          <p className={styles.heroDesc}>
            Automated resume screening, semantic skill matching, and intelligent candidate ranking — 
            powered by large language models.
          </p>
          <div className={styles.heroActions}>
            <Button icon="🚀" onClick={() => navigate('/upload')}>
              Start Screening
            </Button>
            <Button variant="secondary" onClick={() => navigate('/results')}>
              View Rankings
            </Button>
          </div>
        </div>
        <div className={styles.heroVisual}>
          <div className={styles.heroOrb} />
          <div className={styles.heroOrb2} />
          <div className={styles.heroStats}>
            <div className={styles.heroStat}>
              <span className={styles.heroStatValue}>{totalCandidates}</span>
              <span className={styles.heroStatLabel}>Screened</span>
            </div>
            <div className={styles.heroStatDivider} />
            <div className={styles.heroStat}>
              <span className={styles.heroStatValue}>{avgScore}%</span>
              <span className={styles.heroStatLabel}>Avg Match</span>
            </div>
            <div className={styles.heroStatDivider} />
            <div className={styles.heroStat}>
              <span className={styles.heroStatValue}>{strongHireCount}</span>
              <span className={styles.heroStatLabel}>Strong Hires</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Active JD Card ──────────────────────────────────── */}
      {jobTitle && (
        <Card hoverable>
          <div className={styles.jdCard}>
            <div className={styles.jdInfo}>
              <span className={styles.jdBadge}>Active Job Description</span>
              <h2 className={styles.jdTitle}>{jobTitle}</h2>
              <p className={styles.jdMeta}>
                Pipeline status:&nbsp;
                <span className={styles.jdStatus}>Active</span>
                &nbsp;·&nbsp;{totalCandidates} candidates processed
              </p>
            </div>
            <Button onClick={() => navigate('/results')} variant="secondary">
              View Results
            </Button>
          </div>
        </Card>
      )}

      {/* ── Metric Cards ─────────────────────────────────────── */}
      <div className={styles.metricsGrid}>
        <MetricCard icon="👤" value={totalCandidates} label="Total Candidates" accentClass={styles.accentBlue} />
        <MetricCard icon="📈" value={`${avgScore}%`} label="Average Match" accentClass={styles.accentViolet} />
        <MetricCard icon="🏆" value={`${maxScore}%`} label="Highest Score" accentClass={styles.accentGold} />
        <MetricCard icon="🔥" value={strongHireCount} label="Strong Hires" accentClass={styles.accentGreen} />
      </div>

      {/* ── Quick Actions ─────────────────────────────────────── */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Quick Actions</h2>
        <div className={styles.actionsGrid}>
          <ActionCard
            icon="📋"
            step="Step 1"
            title="Setup Screening Pipeline"
            desc="Upload a job description and drag-and-drop candidate resumes (PDF, DOCX, TXT) to kickstart the AI screening process."
            cta="Upload & Configure"
            onClick={() => navigate('/upload')}
          />
          <ActionCard
            icon="🏆"
            step="Step 2"
            title="View Ranked Candidates"
            desc="Browse AI-generated scores, skill overlap percentages, academic credentials, and LLM-powered recommendations."
            cta="Open Rankings"
            onClick={() => navigate('/results')}
            variant="secondary"
          />
          <ActionCard
            icon="📊"
            step="Step 3"
            title="Analytics & Insights"
            desc="Explore score distribution charts, top skill clusters, experience histograms, and download PDF/JSON reports."
            cta="Open Analytics"
            onClick={() => navigate('/analytics')}
            variant="secondary"
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
