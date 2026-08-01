import React, { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Button, EmptyState, ErrorState, Loader, RecommendationBadge } from '../components';
import { XAIService } from '../services/xaiService';
import styles from './XaiPages.module.css';

const chartTooltipStyle = {
  background: 'var(--bg-secondary)',
  border: '1px solid var(--border-color)',
  color: 'var(--text-primary)',
};

export const Explainability = () => {
  const [rankings, setRankings] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadResults = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await XAIService.getResults();
      const rows = response.data?.rankings || [];
      setRankings(rows);
      setSelectedId((current) => current || rows[0]?.candidate_id || '');
    } catch (e) {
      setError(e.message || 'Failed to load screening results.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    setLoading(true);
    setError('');
    XAIService.getCandidateExplanation(selectedId)
      .then((response) => {
        if (active) setExplanation(response.data);
      })
      .catch((e) => {
        if (active) setError(e.message || 'Failed to load candidate explainability.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectedId, reloadKey]);

  const contributionRows = useMemo(
    () => explanation?.score_contributions?.filter((item) => item.maximum_points > 0) || [],
    [explanation]
  );

  if (loading && !explanation) return <Loader text="Loading explainability signals..." />;
  if (error) return <ErrorState description={error} retryAction={loadResults} />;
  if (!rankings.length) {
    return <EmptyState title="No Explainability Data" description="Run screening before reviewing candidate decision explanations." />;
  }

  const mapping = explanation?.requirement_mapping || { fully_matched: [], partially_matched: [], missing: [] };
  const quality = explanation?.resume_quality;
  const confidence = explanation?.confidence_explanation;

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <div>
          <h2 className={styles.panelTitle}>Candidate Decision Explanation</h2>
          <p className={styles.muted}>Transparent score contributions, requirement evidence, confidence, and trace data.</p>
        </div>
        <div className={styles.controls}>
          <select className={styles.select} value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
            {rankings.map((candidate) => (
              <option key={candidate.candidate_id} value={candidate.candidate_id}>
                {candidate.rank}. {candidate.candidate_name}
              </option>
            ))}
          </select>
          <Button variant="secondary" onClick={() => setReloadKey((value) => value + 1)}>
            Refresh
          </Button>
        </div>
      </div>

      {explanation && (
        <>
          <div className={styles.statsGrid}>
            <div className={styles.statBox}>
              <span className={styles.statValue}>{explanation.overall_score}%</span>
              <span className={styles.statLabel}>Overall Score</span>
            </div>
            <div className={styles.statBox}>
              <span className={styles.statValue}>{confidence?.confidence_score}%</span>
              <span className={styles.statLabel}>Confidence</span>
            </div>
            <div className={styles.statBox}>
              <span className={styles.statValue}>{quality?.rating}</span>
              <span className={styles.statLabel}>Resume Quality</span>
            </div>
            <div className={styles.statBox}>
              <RecommendationBadge recommendation={explanation.recommendation} />
              <span className={styles.statLabel}>Recommendation</span>
            </div>
          </div>

          <section className={styles.panel}>
            <h2 className={styles.panelTitle}>{explanation.candidate_name}</h2>
            <p className={styles.text}>{explanation.recommendation_reasoning}</p>
          </section>

          <div className={styles.gridTwo}>
            <section className={styles.panel}>
              <h2 className={styles.panelTitle}>Score Contribution</h2>
              <div className={styles.chartBox}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={contributionRows} layout="vertical">
                    <XAxis type="number" stroke="var(--text-muted)" />
                    <YAxis dataKey="section" type="category" width={120} stroke="var(--text-muted)" fontSize={11} />
                    <ChartTooltip contentStyle={chartTooltipStyle} />
                    <Bar dataKey="earned_points" name="Earned Points" fill="#10b981" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="maximum_points" name="Maximum Points" fill="#6366f1" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className={styles.panel}>
              <h2 className={styles.panelTitle}>Radar View</h2>
              <div className={styles.chartBox}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={explanation.visual_data?.radar || []}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                    <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.28} />
                    <ChartTooltip contentStyle={chartTooltipStyle} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>

          <section className={styles.panel}>
            <h2 className={styles.panelTitle}>Requirement Coverage</h2>
            <div className={styles.gridTwo}>
              <div>
                <p className={styles.muted}>Fully Matched</p>
                <div className={styles.tagList}>
                  {mapping.fully_matched.map((item) => <span key={item.requirement} className={styles.tag}>{item.requirement}</span>)}
                </div>
              </div>
              <div>
                <p className={styles.muted}>Partially Matched</p>
                <div className={styles.tagList}>
                  {mapping.partially_matched.map((item) => <span key={item.requirement} className={styles.tag}>{item.requirement}</span>)}
                </div>
              </div>
            </div>
            <p className={styles.muted}>Missing</p>
            <div className={styles.tagList}>
              {mapping.missing.map((item) => <span key={item.requirement} className={styles.tag}>{item.requirement}</span>)}
            </div>
          </section>

          <div className={styles.gridTwo}>
            <section className={styles.panel}>
              <h2 className={styles.panelTitle}>Resume Quality Analysis</h2>
              <div className={styles.qualityGrid}>
                {quality && Object.entries({
                  Completeness: `${quality.completeness}%`,
                  Formatting: quality.formatting,
                  Contact: quality.contact_information,
                  Projects: quality.project_details,
                  Education: quality.education_quality,
                  Experience: quality.experience_quality,
                }).map(([label, value]) => (
                  <div key={label} className={styles.qualityItem}>
                    <span className={styles.qualityLabel}>{label}</span>
                    <span className={styles.qualityValue}>{value}</span>
                  </div>
                ))}
              </div>
              <div className={styles.tagList}>
                {(quality?.missing_sections || []).map((item) => <span key={item} className={styles.tag}>Missing {item}</span>)}
              </div>
            </section>

            <section className={styles.panel}>
              <h2 className={styles.panelTitle}>Confidence Explanation</h2>
              <p className={styles.text}>{confidence?.explanation}</p>
              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead><tr><th>Factor</th><th>Value</th><th>Explanation</th></tr></thead>
                  <tbody>
                    {(confidence?.factors || []).map((factor) => (
                      <tr key={factor.section}>
                        <td>{factor.section}</td>
                        <td>{factor.percentage}%</td>
                        <td>{factor.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <section className={styles.panel}>
            <h2 className={styles.panelTitle}>AI Trace</h2>
            <div className={styles.timeline}>
              {explanation.ai_trace.map((step) => (
                <div key={`${step.execution_order}-${step.name}`} className={styles.rowCard}>
                  <span className={styles.order}>{step.execution_order}</span>
                  <div>
                    <div className={styles.rowHeader}>
                      <span className={styles.rowTitle}>{step.name}</span>
                      <span className={styles.tag}>{step.execution_time}s</span>
                    </div>
                    <p className={styles.muted}>Status {step.status} | Input {step.input_size} | Output {step.output_size}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default Explainability;
