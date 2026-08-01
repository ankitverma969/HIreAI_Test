import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
  AreaChart,
  Area
} from 'recharts';
import { useCandidates } from '../context/CandidateContext';
import { ChartCard, Button, EmptyState, Loader, ErrorState } from '../components';
import styles from './Analytics.module.css';

const CHART_COLORS = ['#6366f1', '#a855f7', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

export const Analytics = () => {
  const navigate = useNavigate();
  const { rankings, isLoadingResults, errorResults, fetchResults } = useCandidates();

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // 1. Compile chart data packages
  const analyticsData = useMemo(() => {
    if (rankings.length === 0) return null;

    // A. Score & Similarity Averages
    let totalScore = 0;
    let totalSkillMatch = 0;
    let totalSim = 0;
    
    // B. Score Distribution
    const scoreBins = [
      { name: '0-50', count: 0 },
      { name: '50-60', count: 0 },
      { name: '60-70', count: 0 },
      { name: '70-80', count: 0 },
      { name: '80-90', count: 0 },
      { name: '90-100', count: 0 }
    ];

    // C. Recommendation Distribution
    const recMap = { 'Strong Hire': 0, 'Hire': 0, 'Consider': 0, 'Review': 0, 'Reject': 0 };

    // D. Experience Distribution
    const expBins = [
      { name: '0-2 Yrs', count: 0 },
      { name: '2-5 Yrs', count: 0 },
      { name: '5-8 Yrs', count: 0 },
      { name: '8+ Yrs', count: 0 }
    ];

    // E. Skills aggregates
    const skillsMatchedCount = {};
    const skillsMissingCount = {};

    rankings.forEach((r) => {
      const overall = r.score.overall_score;
      totalScore += overall;
      totalSkillMatch += r.score.breakdown.skill_match;
      totalSim += r.score.breakdown.semantic_similarity;

      // Score ranges
      if (overall >= 90) scoreBins[5].count++;
      else if (overall >= 80) scoreBins[4].count++;
      else if (overall >= 70) scoreBins[3].count++;
      else if (overall >= 60) scoreBins[2].count++;
      else if (overall >= 50) scoreBins[1].count++;
      else scoreBins[0].count++;

      // Recommendations
      const reason = (r.score.reasoning || '').toLowerCase();
      if (reason.includes('strong hire') || overall >= 90) recMap['Strong Hire']++;
      else if (reason.includes('reject')) recMap['Reject']++;
      else if (reason.includes('consider')) recMap['Consider']++;
      else if (reason.includes('review')) recMap['Review']++;
      else recMap['Hire']++;

      // Skills overlap counts
      r.score.matched_skills.forEach((s) => {
        skillsMatchedCount[s] = (skillsMatchedCount[s] || 0) + 1;
      });
      r.score.missing_skills.forEach((s) => {
        skillsMissingCount[s] = (skillsMissingCount[s] || 0) + 1;
      });
    });

    const total = rankings.length;

    // F. Transform Skills maps to top 6 lists
    const topSkillsData = Object.entries(skillsMatchedCount)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);

    const topMissingSkillsData = Object.entries(skillsMissingCount)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);

    // G. Transform Recommendation map to pie list
    const recData = Object.entries(recMap)
      .map(([name, value]) => ({ name, value }))
      .filter((item) => item.value > 0);

    return {
      avgScore: Math.round(totalScore / total),
      avgSkillMatch: Math.round(totalSkillMatch / total),
      avgSim: Math.round(totalSim / total),
      scoreBins,
      recData,
      topSkillsData,
      topMissingSkillsData
    };
  }, [rankings]);

  if (isLoadingResults) {
    return <Loader text="Analyzing candidate scores metrics graphs..." />;
  }

  if (errorResults) {
    return <ErrorState retryAction={fetchResults} description={errorResults} />;
  }

  if (rankings.length === 0 || !analyticsData) {
    return (
      <EmptyState
        title="Analytics Data Not Found"
        description="Run the AI resume screening process to view match distribution metrics charts."
        action={
          <Button onClick={() => navigate('/upload')} icon="📋">
            Screen Resumes
          </Button>
        }
      />
    );
  }

  const {
    avgScore,
    avgSkillMatch,
    avgSim,
    scoreBins,
    recData,
    topSkillsData,
    topMissingSkillsData
  } = analyticsData;

  return (
    <div>
      {/* Top Aggregates row */}
      <div className={styles.statsRow}>
        <div className={styles.statBox}>
          <span className={styles.statVal}>{avgScore}%</span>
          <span className={styles.statLabel}>Average Match</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statVal}>{avgSkillMatch}%</span>
          <span className={styles.statLabel}>Average Skills Match</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statVal}>{avgSim}%</span>
          <span className={styles.statLabel}>Semantic Cosine Similarity</span>
        </div>
      </div>

      {/* Grid of charts */}
      <div className={styles.grid}>
        {/* Score distribution Area chart */}
        <ChartCard title="Overall Score Distribution Spread">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={scoreBins}>
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} allowDecimals={false} />
              <ChartTooltip
                contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              />
              <Area type="monotone" dataKey="count" name="Candidates" stroke="#6366f1" fill="rgba(99, 102, 241, 0.15)" strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Recommendation pie chart */}
        <ChartCard title="Recruiter Decision Spread">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={recData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {recData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <ChartTooltip
                contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              />
              <Legend verticalAlign="bottom" height={36} fontSize={11} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Top matched skills bar chart */}
        <ChartCard title="Top Matching Skills Found">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topSkillsData} layout="vertical">
              <XAxis type="number" stroke="var(--text-muted)" fontSize={11} allowDecimals={false} />
              <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} width={80} />
              <ChartTooltip
                contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              />
              <Bar dataKey="count" name="Matches" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Top missing skills bar chart */}
        <ChartCard title="Top Missing Required Skills">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topMissingSkillsData} layout="vertical">
              <XAxis type="number" stroke="var(--text-muted)" fontSize={11} allowDecimals={false} />
              <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} width={80} />
              <ChartTooltip
                contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              />
              <Bar dataKey="count" name="Missing Counts" fill="#ef4444" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
};

export default Analytics;
