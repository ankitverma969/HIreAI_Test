import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNotifications } from '../context/NotificationContext';
import { Card, Button, Input } from '../components';
import styles from './Settings.module.css';

export const Settings = () => {
  const { showSuccess } = useNotifications();

  // Load defaults from local storage
  const defaultValues = {
    llmModel: localStorage.getItem('llmModel') || 'gpt-4o-mini',
    embeddingModel: localStorage.getItem('embeddingModel') || 'all-MiniLM-L6-v2',
    temperature: parseFloat(localStorage.getItem('temperature') || '0.0'),
    serverUrl: localStorage.getItem('serverUrl') || 'http://localhost:8000',
  };

  const { register, handleSubmit, reset } = useForm({
    defaultValues
  });

  const onSubmit = (data) => {
    // Save to local storage
    localStorage.setItem('llmModel', data.llmModel);
    localStorage.setItem('embeddingModel', data.embeddingModel);
    localStorage.setItem('temperature', String(data.temperature));
    localStorage.setItem('serverUrl', data.serverUrl);
    showSuccess('Settings configurations saved successfully!');
  };

  const handleReset = () => {
    localStorage.removeItem('llmModel');
    localStorage.removeItem('embeddingModel');
    localStorage.removeItem('temperature');
    localStorage.removeItem('serverUrl');
    
    reset({
      llmModel: 'gpt-4o-mini',
      embeddingModel: 'all-MiniLM-L6-v2',
      temperature: 0.0,
      serverUrl: 'http://localhost:8000',
    });
    showSuccess('Configurations reset to factory defaults.');
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>System Configuration Settings</h2>
      <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
        {/* API Server URL */}
        <Input
          label="FastAPI Backend Endpoint URL"
          placeholder="e.g. http://localhost:8000"
          {...register('serverUrl')}
        />

        {/* Model option */}
        <div className={styles.row}>
          <label className={styles.label}>AI Recruiter Model Architecture</label>
          <select className={styles.select} {...register('llmModel')} aria-label="Select LLM Model Architecture">
            <option value="gpt-4o-mini">GPT-4o Mini (Default)</option>
            <option value="gpt-4o">GPT-4o (Premium reasoning)</option>
            <option value="gemini-1.5-flash">Gemini 1.5 Flash (Fast completions)</option>
            <option value="gemini-1.5-pro">Gemini 1.5 Pro (Multimodal reasoning)</option>
            <option value="llama-3-70b-groq">Llama 3 70B - Groq (Low latency)</option>
            <option value="mixtral-8x7b-groq">Mixtral 8x7B - Groq (Open weights)</option>
          </select>
        </div>

        {/* Embedding option */}
        <div className={styles.row}>
          <label className={styles.label}>Embedding Transformer Model</label>
          <select className={styles.select} {...register('embeddingModel')} aria-label="Select Embedding Transformer Model">
            <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (Local numpy-scaled)</option>
            <option value="text-embedding-3-small">text-embedding-3-small (OpenAI cloud)</option>
          </select>
        </div>

        {/* Temperature slider */}
        <div className={styles.row}>
          <label className={styles.label}>LLM Generation Temperature</label>
          <input
            type="range"
            min="0.0"
            max="1.0"
            step="0.1"
            style={{ width: '100%', accentColor: 'var(--primary-color)' }}
            {...register('temperature')}
            aria-label="Adjust LLM Generation Temperature"
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', fontWeight: 600 }}>
            Increasing temperature generates more creative summaries; 0.0 is deterministic and recommended for score metrics.
          </span>
        </div>

        {/* Actions panel */}
        <div className={styles.actions}>
          <Button variant="secondary" onClick={handleReset}>
            Reset Defaults
          </Button>
          <Button type="submit">
            Save Settings
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
