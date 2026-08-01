import React, { useEffect, useMemo, useState } from 'react';
import { EmptyState, ErrorState, Loader } from '../components';
import { XAIService } from '../services/xaiService';
import styles from './XaiPages.module.css';

export const PromptInspector = () => {
  const [records, setRecords] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadPrompts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await XAIService.getPromptHistory();
      const rows = response.data?.records || [];
      setRecords(rows);
      setSelectedId((current) => current || rows[0]?.id || '');
    } catch (e) {
      setError(e.message || 'Failed to load prompt history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrompts();
  }, []);

  const selected = useMemo(
    () => records.find((record) => record.id === selectedId) || records[0],
    [records, selectedId]
  );

  if (loading) return <Loader text="Loading sanitized prompt history..." />;
  if (error) return <ErrorState description={error} retryAction={loadPrompts} />;
  if (!records.length) {
    return <EmptyState title="No Prompt History" description="Prompt records appear after screening or inspector initialization." />;
  }

  return (
    <div className={styles.page}>
      <div className={styles.statsGrid}>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{records.length}</span>
          <span className={styles.statLabel}>Prompt Records</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{selected?.execution_time || 0}s</span>
          <span className={styles.statLabel}>Execution Time</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{selected?.token_usage?.prompt_tokens || 0}</span>
          <span className={styles.statLabel}>Prompt Tokens</span>
        </div>
        <div className={styles.statBox}>
          <span className={styles.statValue}>{selected?.token_usage?.completion_tokens || 0}</span>
          <span className={styles.statLabel}>Completion Tokens</span>
        </div>
      </div>

      <div className={styles.promptLayout}>
        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>Prompt History</h2>
          <div className={styles.promptList}>
            {records.map((record) => (
              <button
                key={record.id}
                className={`${styles.promptButton} ${record.id === selected?.id ? styles.promptButtonActive : ''}`}
                onClick={() => setSelectedId(record.id)}
              >
                <strong>{record.prompt_name}</strong>
                <br />
                <span className={styles.muted}>{new Date(record.timestamp).toLocaleString()}</span>
              </button>
            ))}
          </div>
        </section>

        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>{selected?.prompt_name}</h2>
          <p className={styles.muted}>Prompt</p>
          <pre className={styles.promptBody}>{selected?.prompt}</pre>
          <p className={styles.muted}>LLM Response</p>
          <pre className={styles.promptBody}>{selected?.llm_response}</pre>
          <p className={styles.muted}>Structured Output</p>
          <pre className={styles.promptBody}>{JSON.stringify(selected?.structured_output || {}, null, 2)}</pre>
        </section>
      </div>
    </div>
  );
};

export default PromptInspector;
