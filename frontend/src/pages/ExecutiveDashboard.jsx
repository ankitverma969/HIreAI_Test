import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as ChartTooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { Button, EmptyState, ErrorState, Loader, RecommendationBadge } from '../components';
import { ExecutiveService } from '../services/executiveService';
import styles from './ExecutiveDashboard.module.css';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

export const ExecutiveDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [summaryResponse, analyticsResponse] = await Promise.all([
        ExecutiveService.getExecutiveSummary(),
        ExecutiveService.getAnalytics(),
      ]);
      setSummary(summaryResponse.data);
      setAnalytics(analyticsResponse.data);
    } catch (e) {
      setError(e.message || 'Failed to load executive hiring intelligence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <Loader text="Generating executive hiring intelligence..." />;
  if (error) return <ErrorState description={error} retryAction={loadData} />;
  if (!summary || !analytics || analytics.total_candidates === 0) {
    return <EmptyState title="No Executive Data Available" description="Run screening before opening executive intelligence." />;
  }

  return (
    <div className={styles.page}>
      <div className={styles.statsGrid}>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{analytics.total_candidates}</span>
          <span className={styles.statLabel}>Candidates</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{analytics.average_resume_score}%</span>
          <span className={styles.statLabel}>Average Resume Score</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{summary.average_experience}</span>
          <span className={styles.statLabel}>Average Experience Years</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{summary.average_skill_match}%</span>
          <span className={styles.statLabel}>Average Skill Match</span>
        </div>
      </div>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Overall Hiring Summary</h2>
        <p className={styles.summaryText}>{summary.overall_hiring_summary}</p>
        <div className={styles.tagList}>
          <span className={styles.tag}>{summary.overall_recommendation}</span>
          <span className={styles.tag}>{analytics.job_title || 'Role not listed'}</span>
        </div>
      </section>

      <div className={styles.gridTwo}>
        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>Recommendation Distribution</h2>
          <div className={styles.chartBox}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={analytics.recommendation_distribution} dataKey="count" nameKey="name" outerRadius={95}>
                  {analytics.recommendation_distribution.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Legend />
                <ChartTooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>Top Skills</h2>
          <div className={styles.chartBox}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary.top_skills.slice(0, 8)} layout="vertical">
                <XAxis type="number" stroke="var(--text-muted)" allowDecimals={false} />
                <YAxis dataKey="name" type="category" stroke="var(--text-muted)" width={95} fontSize={11} />
                <ChartTooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} />
                <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Top 5 Candidates</h2>
        <div className={styles.candidateList}>
          {summary.top_candidates.map((candidate) => (
            <div key={candidate.candidate_id} className={styles.candidateRow}>
              <div className={styles.rowHeader}>
                <span className={styles.name}>#{candidate.rank} {candidate.candidate_name}</span>
                <RecommendationBadge recommendation={candidate.recommendation} />
              </div>
              <div className={styles.tagList}>
                <span className={styles.tag}>Score {candidate.overall_score}%</span>
                <span className={styles.tag}>Skills {candidate.skill_match}%</span>
                <span className={styles.tag}>Confidence {candidate.confidence_score}%</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Interview Priorities</h2>
        <div className={styles.buttonRow}>
          {summary.interview_priorities.map((priority) => (
            <span key={priority} className={styles.tag}>{priority}</span>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Available Diversity Signals</h2>
        <p className={styles.muted}>Only explicit resume metadata is shown. Protected characteristics are not inferred.</p>
        <div className={styles.tagList}>
          {summary.diversity_metrics.locations.map((item) => (
            <span key={`loc-${item.name}`} className={styles.tag}>Location: {item.name} ({item.count})</span>
          ))}
          {summary.diversity_metrics.languages.map((item) => (
            <span key={`lang-${item.name}`} className={styles.tag}>Language: {item.name} ({item.count})</span>
          ))}
          {summary.diversity_metrics.education_levels.map((item) => (
            <span key={`edu-${item.name}`} className={styles.tag}>Education: {item.name} ({item.count})</span>
          ))}
        </div>
      </section>
    </div>
  );
};

export default ExecutiveDashboard;
