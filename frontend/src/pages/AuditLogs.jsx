import React, { useEffect, useState } from 'react';
import { Button, EmptyState, ErrorState, Loader, RecommendationBadge } from '../components';
import { XAIService } from '../services/xaiService';
import styles from './XaiPages.module.css';

export const AuditLogs = () => {
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState('');
  const [recommendation, setRecommendation] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [order, setOrder] = useState('desc');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadAudit = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await XAIService.getAuditLog({ search, recommendation, sort_by: sortBy, order });
      setRecords(response.data?.records || []);
    } catch (e) {
      setError(e.message || 'Failed to load audit records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, [sortBy, order, recommendation]);

  if (loading && !records.length) return <Loader text="Loading decision audit trail..." />;
  if (error) return <ErrorState description={error} retryAction={loadAudit} />;

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <div>
          <h2 className={styles.panelTitle}>Decision Audit Log</h2>
          <p className={styles.muted}>Timestamped candidate decisions with model, weights, similarity signals, and recommendation.</p>
        </div>
        <div className={styles.controls}>
          <input className={styles.input} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search candidate or JD" />
          <select className={styles.select} value={recommendation} onChange={(event) => setRecommendation(event.target.value)}>
            <option value="">All Recommendations</option>
            <option value="Strong Hire">Strong Hire</option>
            <option value="Hire">Hire</option>
            <option value="Consider">Consider</option>
            <option value="Review">Review</option>
            <option value="Reject">Reject</option>
          </select>
          <select className={styles.select} value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="timestamp">Timestamp</option>
            <option value="candidate_name">Candidate</option>
            <option value="recommendation">Recommendation</option>
            <option value="jd_id">JD ID</option>
          </select>
          <select className={styles.select} value={order} onChange={(event) => setOrder(event.target.value)}>
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
          <Button variant="secondary" onClick={loadAudit}>Search</Button>
          <Button onClick={() => XAIService.downloadAuditCsv({ search, recommendation, sort_by: sortBy, order })}>Export CSV</Button>
        </div>
      </div>

      {!records.length ? (
        <EmptyState title="No Audit Records" description="Run screening before opening the audit trail." />
      ) : (
        <section className={styles.panel}>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Candidate</th>
                  <th>JD ID</th>
                  <th>Recommendation</th>
                  <th>Model</th>
                  <th>Embedding</th>
                  <th>Similarity</th>
                  <th>Weights</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={`${record.candidate_id}-${record.timestamp}`}>
                    <td>{new Date(record.timestamp).toLocaleString()}</td>
                    <td>{record.candidate_name}<br /><span className={styles.muted}>{record.candidate_id}</span></td>
                    <td>{record.jd_id}</td>
                    <td><RecommendationBadge recommendation={record.recommendation} /></td>
                    <td>{record.model_used}</td>
                    <td>{record.embedding_model}</td>
                    <td>{Object.entries(record.similarity_scores || {}).map(([key, value]) => `${key}: ${value}`).join(', ')}</td>
                    <td>{Object.entries(record.weights_used || {}).map(([key, value]) => `${key}: ${value}`).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
};

export default AuditLogs;
