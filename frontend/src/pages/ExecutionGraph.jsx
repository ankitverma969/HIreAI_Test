import React, { useEffect, useState } from 'react';
import { Bar, BarChart, ResponsiveContainer, Tooltip as ChartTooltip, XAxis, YAxis } from 'recharts';
import { EmptyState, ErrorState, Loader } from '../components';
import { XAIService } from '../services/xaiService';
import styles from './XaiPages.module.css';

export const ExecutionGraph = () => {
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadGraph = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await XAIService.getGraphExecution();
      setGraph(response.data);
    } catch (e) {
      setError(e.message || 'Failed to load graph observability data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  if (loading) return <Loader text="Loading LangGraph execution timeline..." />;
  if (error) return <ErrorState description={error} retryAction={loadGraph} />;
  if (!graph?.timeline?.length) {
    return <EmptyState title="No Graph Execution" description="Run screening before reviewing LangGraph observability." />;
  }

  const metrics = graph.performance_metrics || {};

  return (
    <div className={styles.page}>
      <div className={styles.statsGrid}>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{metrics.total_execution_time || 0}s</span>
          <span className={styles.statLabel}>Total Latency</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{metrics.node_count || graph.timeline.length}</span>
          <span className={styles.statLabel}>Nodes</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{metrics.average_node_time || 0}s</span>
          <span className={styles.statLabel}>Average Node Time</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{metrics.retry_count || 0}</span>
          <span className={styles.statLabel}>Retries</span>
        </div>
      </div>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Node Latency</h2>
        <div className={styles.chartBox}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={graph.timeline}>
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-20} textAnchor="end" height={72} />
              <YAxis stroke="var(--text-muted)" />
              <ChartTooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} />
              <Bar dataKey="execution_time" name="Execution Time" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className={styles.panel}>
        <h2 className={styles.panelTitle}>Execution Timeline</h2>
        <div className={styles.timeline}>
          {graph.timeline.map((step) => (
            <div key={`${step.execution_order}-${step.name}`} className={styles.rowCard}>
              <span className={styles.order}>{step.execution_order}</span>
              <div>
                <div className={styles.rowHeader}>
                  <span className={styles.rowTitle}>{step.name}</span>
                  <span className={styles.tag}>{step.status}</span>
                </div>
                <p className={styles.muted}>
                  {step.execution_time}s | Input {step.input_size} | Output {step.output_size} | Retries {step.retry_count}
                </p>
                {step.failure_reason && <p className={styles.text}>{step.failure_reason}</p>}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default ExecutionGraph;
