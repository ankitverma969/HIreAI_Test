import React, { useEffect, useState } from 'react';
import { EmptyState, ErrorState, Loader } from '../components';
import { ExecutiveService } from '../services/executiveService';
import styles from './ExecutiveDashboard.module.css';

export const HiringInsights = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await ExecutiveService.getInsights();
      setInsights(response.data);
    } catch (e) {
      setError(e.message || 'Failed to load hiring insights.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) return <Loader text="Generating hiring insights..." />;
  if (error) return <ErrorState description={error} retryAction={loadData} />;
  if (!insights) return <EmptyState title="No Hiring Insights Available" description="Run screening before opening insights." />;

  return (
    <div className={styles.page}>
      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Team Fit Analysis</h2>
        <div className={styles.fitList}>
          {insights.team_fit.map((fit) => (
            <div key={fit.category} className={styles.fitBox}>
              <div className={styles.rowHeader}>
                <span className={styles.name}>{fit.category}</span>
                <span className={styles.muted}>{fit.candidate_name || 'No clear candidate'}</span>
              </div>
              <p className={styles.text}>{fit.explanation}</p>
              <div className={styles.tagList}>
                {fit.evidence.map((item) => <span key={item} className={styles.tag}>{item}</span>)}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Hiring Risks</h2>
        <div className={styles.riskList}>
          {insights.risks.map((risk) => (
            <div key={`${risk.category}-${risk.description}`} className={styles.riskBox}>
              <div className={styles.rowHeader}>
                <span className={styles.name}>{risk.category}</span>
                <span className={styles.tag}>{risk.severity}</span>
              </div>
              <p className={styles.text}>{risk.description}</p>
              <p className={styles.text}><strong>Mitigation:</strong> {risk.mitigation}</p>
              {risk.affected_candidates.length > 0 && (
                <div className={styles.tagList}>
                  {risk.affected_candidates.map((candidate) => <span key={candidate} className={styles.tag}>{candidate}</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Interview Planning</h2>
        <div className={styles.planList}>
          {insights.interview_plan.map((item) => (
            <div key={item.candidate_id} className={styles.planBox}>
              <div className={styles.rowHeader}>
                <span className={styles.name}>{item.interview_order}. {item.candidate_name}</span>
                <span className={styles.tag}>{item.expected_difficulty}</span>
              </div>
              <p className={styles.text}><strong>Focus:</strong> {item.focus_areas.join(', ')}</p>
              <p className={styles.text}><strong>Technical:</strong> {item.technical_questions.join(' ')}</p>
              <p className={styles.text}><strong>Behavioral:</strong> {item.behavioral_questions.join(' ')}</p>
              <p className={styles.text}><strong>Red flags:</strong> {item.red_flags.join(' ')}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default HiringInsights;
