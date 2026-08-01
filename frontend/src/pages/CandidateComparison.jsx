import React, { useEffect, useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as ChartTooltip,
  Legend,
} from 'recharts';
import { useCandidates } from '../context/CandidateContext';
import { useNotifications } from '../context/NotificationContext';
import { ComparisonService } from '../services/comparisonService';
import { Button, EmptyState, Loader, RecommendationBadge, SkillBadge } from '../components';
import styles from './CandidateComparison.module.css';

const COLORS = ['#6366f1', '#10b981', '#f59e0b'];

export const CandidateComparison = () => {
  const { rankings, fetchResults, isLoadingResults } = useCandidates();
  const { showError, showSuccess } = useNotifications();
  const [selectedIds, setSelectedIds] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [isComparing, setIsComparing] = useState(false);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const candidateOptions = useMemo(() => {
    return rankings.map((ranking) => ({
      id: ranking.candidate_id,
      name: ranking.candidate_name,
      score: ranking.score.overall_score,
      rank: ranking.rank,
    }));
  }, [rankings]);

  const toggleCandidate = (candidateId) => {
    setSelectedIds((prev) => {
      if (prev.includes(candidateId)) {
        return prev.filter((id) => id !== candidateId);
      }
      if (prev.length >= 3) {
        showError('Select a maximum of 3 candidates.');
        return prev;
      }
      return [...prev, candidateId];
    });
  };

  const handleCompare = async () => {
    if (selectedIds.length < 2 || selectedIds.length > 3) {
      showError('Select 2 or 3 candidates to compare.');
      return;
    }

    setIsComparing(true);
    try {
      const response = await ComparisonService.compare(selectedIds);
      setComparison(response.data);
      showSuccess('Candidate comparison generated.');
    } catch (e) {
      showError(e.message || 'Failed to compare candidates.');
    } finally {
      setIsComparing(false);
    }
  };

  if (isLoadingResults) {
    return <Loader text="Loading candidates for comparison..." />;
  }

  if (!rankings.length) {
    return (
      <EmptyState
        title="No Candidates Available"
        description="Run a screening workflow before comparing candidates."
      />
    );
  }

  const items = comparison?.candidates || [];
  const radarData = comparison?.chart_data?.radar || [];
  const barData = comparison?.chart_data?.bars || [];
  const heatmap = comparison?.chart_data?.skill_heatmap || [];
  const highlights = comparison?.highlights || {};

  return (
    <div className={styles.page}>
      <section className={styles.selectorPanel}>
        <div>
          <h2 className={styles.panelTitle}>Select Candidates</h2>
          <p className={styles.panelSub}>Choose 2 or 3 ranked candidates for a side-by-side assistant review.</p>
        </div>

        <div className={styles.candidateGrid}>
          {candidateOptions.map((candidate) => {
            const active = selectedIds.includes(candidate.id);
            return (
              <button
                key={candidate.id}
                className={`${styles.candidateOption} ${active ? styles.selected : ''}`}
                type="button"
                onClick={() => toggleCandidate(candidate.id)}
              >
                <span className={styles.rank}>#{candidate.rank}</span>
                <span className={styles.name}>{candidate.name}</span>
                <span className={styles.score}>{candidate.score}%</span>
              </button>
            );
          })}
        </div>

        <div className={styles.actions}>
          <span className={styles.selectionCount}>{selectedIds.length}/3 selected</span>
          <Button onClick={handleCompare} loading={isComparing} disabled={selectedIds.length < 2}>
            Compare Candidates
          </Button>
        </div>
      </section>

      {comparison && (
        <>
          <section className={styles.highlights}>
            <div className={styles.highlightBox}>
              <span>Best Candidate</span>
              <strong>{highlights.best_candidate_name}</strong>
            </div>
            <div className={styles.highlightBox}>
              <span>Most Experienced</span>
              <strong>{highlights.most_experienced_name}</strong>
            </div>
            <div className={styles.highlightBox}>
              <span>Highest Skill Match</span>
              <strong>{highlights.highest_skill_match_name}</strong>
            </div>
            <div className={styles.highlightBox}>
              <span>Most Complete Resume</span>
              <strong>{highlights.most_complete_resume_name}</strong>
            </div>
          </section>

          <section className={styles.summaryPanel}>
            <h2 className={styles.panelTitle}>Executive Comparison</h2>
            <div className={styles.summaryGrid}>
              <p><strong>Overview:</strong> {comparison.ai_summary.executive_comparison}</p>
              <p><strong>Ranking rationale:</strong> {comparison.ai_summary.why_ranked_higher}</p>
              <p><strong>Strengths:</strong> {comparison.ai_summary.strength_comparison}</p>
              <p><strong>Risks:</strong> {comparison.ai_summary.risk_comparison}</p>
              <p><strong>Interview plan:</strong> {comparison.ai_summary.interview_recommendation}</p>
              <p><strong>Hiring recommendation:</strong> {comparison.ai_summary.hiring_recommendation}</p>
            </div>
          </section>

          <section className={styles.visualGrid}>
            <div className={styles.chartPanel}>
              <h3>Radar Comparison</h3>
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border-color)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                  {items.map((item, index) => (
                    <Radar
                      key={item.candidate_id}
                      name={item.candidate_name}
                      dataKey={item.candidate_name}
                      stroke={COLORS[index % COLORS.length]}
                      fill={COLORS[index % COLORS.length]}
                      fillOpacity={0.16}
                    />
                  ))}
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className={styles.chartPanel}>
              <h3>Score Bars</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={barData}>
                  <XAxis dataKey="candidate_name" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} domain={[0, 100]} />
                  <ChartTooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} />
                  <Legend />
                  <Bar dataKey="overall_score" name="Overall" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="skill_match" name="Skills" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="experience_match" name="Experience" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className={styles.tablePanel}>
            <h2 className={styles.panelTitle}>Comparison Table</h2>
            <div className={styles.tableWrap}>
              <table className={styles.compareTable}>
                <thead>
                  <tr>
                    <th>Metric</th>
                    {items.map((item) => <th key={item.candidate_id}>{item.candidate_name}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['Overall Score', 'overall_score', '%'],
                    ['Skill Match', 'skill_match', '%'],
                    ['Experience', 'total_experience_years', ' yrs'],
                    ['Education', 'education_match', '%'],
                    ['Projects', 'project_match', '%'],
                    ['Certifications', 'certification_match', '%'],
                    ['Semantic Similarity', 'semantic_similarity', '%'],
                    ['Confidence', 'confidence_score', '%'],
                  ].map(([label, key, suffix]) => (
                    <tr key={key}>
                      <td>{label}</td>
                      {items.map((item) => <td key={item.candidate_id}>{item[key]}{suffix}</td>)}
                    </tr>
                  ))}
                  <tr>
                    <td>Recommendation</td>
                    {items.map((item) => (
                      <td key={item.candidate_id}><RecommendationBadge recommendation={item.recommendation} /></td>
                    ))}
                  </tr>
                  <tr>
                    <td>Matched Skills</td>
                    {items.map((item) => (
                      <td key={item.candidate_id}>
                        <div className={styles.skillList}>
                          {item.matched_skills.map((skill) => <SkillBadge key={skill} skill={skill} matched />)}
                        </div>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td>Missing Skills</td>
                    {items.map((item) => (
                      <td key={item.candidate_id}>
                        <div className={styles.skillList}>
                          {item.missing_skills.map((skill) => <SkillBadge key={skill} skill={skill} matched={false} missing />)}
                        </div>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className={styles.heatmapPanel}>
            <h2 className={styles.panelTitle}>Skill Heatmap</h2>
            <div
              className={styles.heatmap}
              style={{ gridTemplateColumns: `minmax(150px, 1.1fr) repeat(${items.length}, minmax(140px, 1fr))` }}
            >
              <div className={styles.heatHeader}>Skill</div>
              {items.map((item) => <div key={item.candidate_id} className={styles.heatHeader}>{item.candidate_name}</div>)}
              {heatmap.map((row) => (
                <React.Fragment key={row.skill}>
                  <div className={styles.skillName}>{row.skill}</div>
                  {items.map((item) => {
                    const value = row[item.candidate_name];
                    return (
                      <div key={item.candidate_id} className={`${styles.heatCell} ${styles[value]}`}>
                        {value === 'matched' ? 'Matched' : value === 'missing' ? 'Missing' : '-'}
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default CandidateComparison;
