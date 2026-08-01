import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNotifications } from '../context/NotificationContext';
import { Card, Button, Input } from '../components';
import styles from './Settings.module.css';

const PROVIDERS = [
  {
    id: 'openai',
    name: 'OpenAI',
    icon: '🟢',
    models: [
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini — Fast & cost-efficient' },
      { value: 'gpt-4o',      label: 'GPT-4o — Premium multimodal reasoning' },
    ],
  },
  {
    id: 'google',
    name: 'Google Gemini',
    icon: '🔵',
    models: [
      { value: 'gemini-3-flash-preview',         label: 'Gemini 3 Flash Preview — Best reasoning/coding' },
      { value: 'gemini-3.1-flash-lite-preview',  label: 'Gemini 3.1 Flash Lite Preview — Extremely fast fallback' },
      { value: 'gemini-2.5-flash',               label: 'Gemini 2.5 Flash — Stable production model' },
      { value: 'gemini-flash-latest',            label: 'Gemini Flash Latest — Standard latest flash' },
      { value: 'gemini-flash-lite-latest',       label: 'Gemini Flash Lite Latest — Ultimate fast fallback' },
    ],
  },
  {
    id: 'groq',
    name: 'Groq (Open Source)',
    icon: '🟠',
    models: [
      { value: 'llama-3-70b-groq',   label: 'Llama 3 70B — Low-latency inference' },
      { value: 'mixtral-8x7b-groq',  label: 'Mixtral 8x7B — Open weights MoE' },
    ],
  },
];

const ALL_MODELS = PROVIDERS.flatMap((p) => p.models);

const getProvider = (modelValue) => {
  for (const p of PROVIDERS) {
    if (p.models.some((m) => m.value === modelValue)) return p;
  }
  return PROVIDERS[0];
};

export const Settings = () => {
  const { showSuccess, showError } = useNotifications();

  const defaultValues = {
    llmModel:       localStorage.getItem('llmModel')       || 'gpt-4o-mini',
    embeddingModel: localStorage.getItem('embeddingModel') || 'all-MiniLM-L6-v2',
    temperature:    parseFloat(localStorage.getItem('temperature') || '0.0'),
    serverUrl:      localStorage.getItem('serverUrl')      || 'http://localhost:8000',
    apiKey:         localStorage.getItem('apiKey')         || '',
    geminiApiBase:  localStorage.getItem('geminiApiBase')  || '',
  };

  const { register, handleSubmit, watch, reset } = useForm({ defaultValues });
  const watchTemp = watch('temperature', defaultValues.temperature);
  const watchModel = watch('llmModel', defaultValues.llmModel);
  const activeProvider = getProvider(watchModel);

  const [saved, setSaved] = useState(false);

  const onSubmit = (data) => {
    try {
      localStorage.setItem('llmModel',       data.llmModel);
      localStorage.setItem('embeddingModel', data.embeddingModel);
      localStorage.setItem('temperature',    String(data.temperature));
      localStorage.setItem('serverUrl',      data.serverUrl);
      if (data.apiKey) localStorage.setItem('apiKey', data.apiKey);
      else localStorage.removeItem('apiKey');
      localStorage.setItem('geminiApiBase',  data.geminiApiBase || '');
      setSaved(true);
      showSuccess('Settings saved — changes take effect immediately.');
      setTimeout(() => setSaved(false), 2500);
    } catch {
      showError('Failed to save settings.');
    }
  };

  const handleReset = () => {
    const defaults = {
      llmModel:       'gpt-4o-mini',
      embeddingModel: 'all-MiniLM-L6-v2',
      temperature:    0.0,
      serverUrl:      'http://localhost:8000',
      geminiApiBase:  '',
      apiKey:         '',
    };
    Object.entries(defaults).forEach(([k, v]) => {
      if (v === '') localStorage.removeItem(k);
      else localStorage.setItem(k, String(v));
    });
    reset(defaults);
    showSuccess('Reset to factory defaults.');
  };

  const isGemini = activeProvider.id === 'google';

  return (
    <div className={styles.page}>
      {/* Page header */}
      <div className={styles.pageHeader}>
        <div className={styles.headerIcon}>⚙️</div>
        <div>
          <h2 className={styles.pageTitle}>System Configuration</h2>
          <p className={styles.pageSubtitle}>
            Manage AI model provider, API connections, and pipeline parameters
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
        {/* ── Section: Backend Connection ─────────────────── */}
        <Card title="Backend Connection" hoverable={false}>
          <div className={styles.fieldGroup}>
            <Input
              label="FastAPI Backend URL"
              placeholder="http://localhost:8000"
              {...register('serverUrl')}
            />
            <Input
              label="API Key (X-API-Key)"
              placeholder="Paste your API key for backend access"
              {...register('apiKey')}
            />
            <p className={styles.hint}>
              The REST + WebSocket server address. Changes apply immediately to all API calls and live pipeline updates.
            </p>
          </div>
        </Card>

        {/* ── Section: LLM Provider ───────────────────────── */}
        <Card title="AI Model Provider">
          {/* Provider tabs */}
          <div className={styles.providerTabs}>
            {PROVIDERS.map((p) => (
              <div
                key={p.id}
                className={`${styles.providerTab} ${activeProvider.id === p.id ? styles.providerTabActive : ''}`}
              >
                <span>{p.icon}</span>
                <span>{p.name}</span>
              </div>
            ))}
          </div>

          <div className={styles.fieldGroup} style={{ marginTop: '20px' }}>
            <label className={styles.fieldLabel}>Model Architecture</label>
            <select
              className={styles.select}
              {...register('llmModel')}
              aria-label="Select LLM Model"
            >
              {PROVIDERS.map((provider) => (
                <optgroup key={provider.id} label={`${provider.icon} ${provider.name}`}>
                  {provider.models.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>

            {/* Active model badge */}
            <div className={styles.activeBadge}>
              <span className={styles.activeDot} />
              <span>Active: <strong>{watchModel}</strong> via {activeProvider.name}</span>
            </div>
          </div>

          {/* Gemini-specific: custom API base URL */}
          {isGemini && (
            <div className={`${styles.fieldGroup} ${styles.geminiBox}`}>
              <Input
                label="Gemini API Base URL (optional)"
                placeholder="e.g. https://generativelanguage.googleapis.com"
                {...register('geminiApiBase')}
              />
              <p className={styles.hint}>
                Override the default Gemini endpoint. Useful for Vertex AI, enterprise gateways, or custom testing URLs.
                Leave blank to use the standard Google API.
              </p>
            </div>
          )}
        </Card>

        {/* ── Section: Pipeline Parameters ────────────────── */}
        <Card title="Pipeline Parameters">
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel}>Embedding Transformer Model</label>
            <select
              className={styles.select}
              {...register('embeddingModel')}
              aria-label="Select Embedding Model"
            >
              <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 — Local, fast semantic matching</option>
              <option value="text-embedding-3-small">text-embedding-3-small — OpenAI cloud embeddings</option>
            </select>
          </div>

          <div className={styles.fieldGroup} style={{ marginTop: '24px' }}>
            <div className={styles.tempHeader}>
              <label className={styles.fieldLabel}>Generation Temperature</label>
              <div className={styles.tempValue}>
                <span className={styles.tempBadge}>{Number(watchTemp).toFixed(1)}</span>
              </div>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              className={styles.rangeSlider}
              {...register('temperature')}
              aria-label="LLM Temperature"
            />
            <div className={styles.rangeLabels}>
              <span>Deterministic (0.0)</span>
              <span>Creative (1.0)</span>
            </div>
            <p className={styles.hint}>
              <strong>Recommended: 0.0</strong> — deterministic output ensures consistent scoring.
              Higher values produce more varied, creative summaries.
            </p>
          </div>
        </Card>

        {/* ── Section: Action Buttons ──────────────────────── */}
        <div className={styles.actions}>
          <Button variant="ghost" type="button" onClick={handleReset}>
            Reset Defaults
          </Button>
          <Button
            type="submit"
            variant={saved ? 'success' : 'primary'}
            icon={saved ? '✅' : '💾'}
          >
            {saved ? 'Saved!' : 'Save Settings'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
