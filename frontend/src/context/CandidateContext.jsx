import React, { createContext, useContext, useState, useCallback } from 'react';
import { CandidateService } from '../services/candidateService';
import { useNotifications } from './NotificationContext';

const CandidateContext = createContext();

export const CandidateProvider = ({ children }) => {
  const { showError } = useNotifications();

  // Results list states
  const [rankings, setRankings] = useState([]);
  const [resultsReportId, setResultsReportId] = useState(null);
  const [jobTitle, setJobTitle] = useState(null);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [errorResults, setErrorResults] = useState(null);

  // Single candidate states
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [selectedCandidateDetails, setSelectedCandidateDetails] = useState(null);
  const [isLoadingCandidate, setIsLoadingCandidate] = useState(false);
  const [errorCandidate, setErrorCandidate] = useState(null);

  const fetchResults = useCallback(async () => {
    setIsLoadingResults(true);
    setErrorResults(null);
    try {
      const response = await CandidateService.getResults();
      // response structure is { success: true, message: "...", data: { report_id, job_title, rankings } }
      if (response && response.data) {
        setRankings(response.data.rankings || []);
        setResultsReportId(response.data.report_id);
        setJobTitle(response.data.job_title);
      }
    } catch (e) {
      setErrorResults(e.message || 'Failed to fetch screening results.');
      showError(e.message || 'Failed to fetch screening results.');
    } finally {
      setIsLoadingResults(false);
    }
  }, [showError]);

  const fetchCandidateDetails = useCallback(async (id) => {
    setIsLoadingCandidate(true);
    setErrorCandidate(null);
    setSelectedCandidateId(id);
    try {
      const response = await CandidateService.getCandidate(id);
      // response structure is { success: true, message: "...", data: { profile: {...}, score: {...} } }
      if (response && response.data) {
        setSelectedCandidateDetails(response.data);
      }
    } catch (e) {
      setErrorCandidate(e.message || 'Failed to fetch candidate details.');
      showError(e.message || 'Failed to fetch candidate details.');
      setSelectedCandidateDetails(null);
    } finally {
      setIsLoadingCandidate(false);
    }
  }, [showError]);

  const clearSelectedCandidate = () => {
    setSelectedCandidateId(null);
    setSelectedCandidateDetails(null);
    setErrorCandidate(null);
  };

  return (
    <CandidateContext.Provider
      value={{
        rankings,
        resultsReportId,
        jobTitle,
        isLoadingResults,
        errorResults,
        selectedCandidateId,
        selectedCandidateDetails,
        isLoadingCandidate,
        errorCandidate,
        fetchResults,
        fetchCandidateDetails,
        setSelectedCandidateId,
        clearSelectedCandidate,
      }}
    >
      {children}
    </CandidateContext.Provider>
  );
};

export const useCandidates = () => {
  const context = useContext(CandidateContext);
  if (!context) {
    throw new Error('useCandidates must be used within a CandidateProvider');
  }
  return context;
};
export default CandidateContext;
