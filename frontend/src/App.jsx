import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { NotificationProvider } from './context/NotificationContext';
import { AnalysisProvider } from './context/AnalysisContext';
import { CandidateProvider } from './context/CandidateContext';
import Layout from './layout/Layout';
import {
  Dashboard,
  Upload,
  Processing,
  Results,
  CandidateDetails,
  CandidateComparison,
  RecruiterChat,
  ExecutiveDashboard,
  HiringInsights,
  Reports,
  Explainability,
  AuditLogs,
  ExecutionGraph,
  PromptInspector,
  Analytics,
  Settings,
  NotFound,
} from './pages';

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <NotificationProvider>
          <AnalysisProvider>
            <CandidateProvider>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/upload" element={<Upload />} />
                  <Route path="/processing" element={<Processing />} />
                  <Route path="/results" element={<Results />} />
                  <Route path="/results/:candidateId" element={<CandidateDetails />} />
                  <Route path="/compare" element={<CandidateComparison />} />
                  <Route path="/chat" element={<RecruiterChat />} />
                  <Route path="/executive" element={<ExecutiveDashboard />} />
                  <Route path="/insights" element={<HiringInsights />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/explainability" element={<Explainability />} />
                  <Route path="/audit" element={<AuditLogs />} />
                  <Route path="/graph" element={<ExecutionGraph />} />
                  <Route path="/prompts" element={<PromptInspector />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Layout>
            </CandidateProvider>
          </AnalysisProvider>
        </NotificationProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
