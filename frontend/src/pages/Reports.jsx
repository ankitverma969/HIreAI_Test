import React, { useEffect, useState } from 'react';
import { Button, EmptyState, ErrorState, Loader } from '../components';
import { ExecutiveService } from '../services/executiveService';
import styles from './ExecutiveDashboard.module.css';

export const Reports = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState('');
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await ExecutiveService.getHiringReport();
      setReport(response.data);
    } catch (e) {
      setError(e.message || 'Failed to generate executive report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDownload = async (format) => {
    setDownloading(format);
    try {
      await ExecutiveService.downloadReport(format);
    } catch (e) {
      setError(e.message || `Failed to download ${format} report.`);
    } finally {
      setDownloading('');
    }
  };

  if (loading) return <Loader text="Preparing executive hiring report..." />;
  if (error) return <ErrorState description={error} retryAction={loadData} />;
  if (!report) return <EmptyState title="No Report Available" description="Run screening before generating executive reports." />;

  const summary = report.executive_summary;
  const analytics = report.analytics;

  return (
    <div className={styles.page}>
      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>One-Click Executive Reports</h2>
        <p className={styles.summaryText}>{summary.overall_hiring_summary}</p>
        <div className={styles.buttonRow} style={{ marginTop: '18px' }}>
          <Button onClick={() => handleDownload('pdf')} loading={downloading === 'pdf'}>Executive PDF</Button>
          <Button variant="secondary" onClick={() => handleDownload('markdown')} loading={downloading === 'markdown'}>Markdown Report</Button>
          <Button variant="secondary" onClick={() => handleDownload('csv')} loading={downloading === 'csv'}>CSV Analytics</Button>
          <Button variant="secondary" onClick={() => handleDownload('json')} loading={downloading === 'json'}>JSON Analytics</Button>
        </div>
      </section>

      <div className={styles.statsGrid}>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{analytics.average_resume_score}%</span>
          <span className={styles.statLabel}>Average Score</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{analytics.average_skill_match}%</span>
          <span className={styles.statLabel}>Skill Match</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{analytics.average_experience}</span>
          <span className={styles.statLabel}>Experience Years</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{analytics.total_candidates}</span>
          <span className={styles.statLabel}>Candidates</span>
        </div>
      </div>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Report Preview</h2>
        <p className={styles.text}><strong>Overall recommendation:</strong> {summary.overall_recommendation}</p>
        <p className={styles.text}><strong>Top candidates:</strong> {summary.top_candidates.map((candidate) => candidate.candidate_name).join(', ')}</p>
        <p className={styles.text}><strong>Top skills:</strong> {summary.top_skills.map((skill) => skill.name).join(', ')}</p>
        <p className={styles.text}><strong>Most missing skills:</strong> {summary.most_missing_skills.map((skill) => skill.name).join(', ') || 'None flagged'}</p>
      </section>
    </div>
  );
};

export default Reports;
