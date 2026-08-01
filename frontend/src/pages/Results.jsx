import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCandidates } from '../context/CandidateContext';
import { usePagination } from '../hooks/usePagination';
import { useSearch } from '../hooks/useSearch';
import {
  Table,
  Pagination,
  SearchBar,
  FilterPanel,
  RecommendationBadge,
  DownloadButton,
  Loader,
  EmptyState,
  ErrorState,
  Button,
} from '../components';
import styles from './Results.module.css';

export const Results = () => {
  const navigate = useNavigate();
  const { rankings, isLoadingResults, errorResults, fetchResults, jobTitle } = useCandidates();

  // Filter States
  const [recommendationFilter, setRecommendationFilter] = useState('All Decisions');
  const [minScoreFilter, setMinScoreFilter] = useState(0);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // 1. Flatten rankings data structure for table sorting & searching
  const flatRankings = useMemo(() => {
    if (!Array.isArray(rankings)) return [];
    return rankings.map((r) => {
      // Deduce recommendation decision category from reasoning text
      const reason = (r?.score?.reasoning || '').toLowerCase();
      let rec = 'Consider';
      if (reason.includes('strong hire')) rec = 'Strong Hire';
      else if (reason.includes('reject')) rec = 'Reject';
      else if (reason.includes('consider')) rec = 'Consider';
      else if (reason.includes('review')) rec = 'Review';
      else if (reason.includes('hire')) rec = 'Hire';

      return {
        id: r.candidate_id,
        candidate_id: r.candidate_id,
        candidate_name: r.candidate_name,
        rank: r.rank,
        overall_score: r?.score?.overall_score ?? 0,
        skill_match: r?.score?.breakdown?.skill_match ?? 0,
        experience_match: r?.score?.breakdown?.experience_match ?? 0,
        education_match: r?.score?.breakdown?.education_match ?? 0,
        semantic_similarity: r?.score?.breakdown?.semantic_similarity ?? 0,
        confidence_score: r?.score?.confidence_score ?? 0,
        recommendation: rec,
        score: r.score
      };
    });
  }, [rankings]);

  // 2. Apply Search
  const { searchQuery, setSearchQuery, filteredItems: searchedRankings } = useSearch(flatRankings, [
    'candidate_name',
    'recommendation'
  ]);

  // 3. Apply Filters
  const filteredRankings = useMemo(() => {
    return searchedRankings.filter((item) => {
      // Recommendation match
      if (recommendationFilter !== 'All Decisions' && item.recommendation !== recommendationFilter) {
        return false;
      }
      // Min score match
      if (item.overall_score < minScoreFilter) {
        return false;
      }
      return true;
    });
  }, [searchedRankings, recommendationFilter, minScoreFilter]);

  // 4. Apply Pagination
  const {
    currentPage,
    pageSize,
    totalPages,
    setPage,
    startIndex,
    endIndex,
  } = usePagination(filteredRankings.length, 10);

  const paginatedRankings = useMemo(() => {
    return filteredRankings.slice(startIndex, endIndex);
  }, [filteredRankings, startIndex, endIndex]);

  // Calculate statistics metrics
  const stats = useMemo(() => {
    const total = Array.isArray(rankings) ? rankings.length : 0;
    if (!total) return { avg: 0, max: 0, strongCount: 0 };

    const avg = Math.round((rankings.reduce((acc, c) => acc + (c?.score?.overall_score ?? 0), 0)) / total);
    const max = Math.max(...rankings.map((r) => r?.score?.overall_score ?? 0));
    
    // Count Strong Hires
    const strongCount = flatRankings.filter(item => item.recommendation === 'Strong Hire').length;

    return { avg, max, strongCount };
  }, [rankings, flatRankings]);

  // Define table column definitions
  const columns = [
    { title: 'Rank', dataIndex: 'rank', sortable: true, width: '80px' },
    { title: 'Candidate Name', dataIndex: 'candidate_name', sortable: true },
    {
      title: 'Overall Score',
      dataIndex: 'overall_score',
      sortable: true,
      render: (val) => <span style={{ fontWeight: 700, color: 'var(--primary-color)' }}>{val}%</span>
    },
    {
      title: 'Skills Overlap',
      dataIndex: 'skill_match',
      sortable: true,
      render: (val) => `${val}%`
    },
    {
      title: 'Experience Align',
      dataIndex: 'experience_match',
      sortable: true,
      render: (val) => `${val}%`
    },
    {
      title: 'Education Match',
      dataIndex: 'education_match',
      sortable: true,
      render: (val) => `${val}%`
    },
    {
      title: 'Semantic Sim',
      dataIndex: 'semantic_similarity',
      sortable: true,
      render: (val) => `${val}%`
    },
    {
      title: 'Decision Recommendation',
      dataIndex: 'recommendation',
      sortable: true,
      render: (val) => <RecommendationBadge recommendation={val} />
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence_score',
      sortable: true,
      render: (val) => `${val}%`
    }
  ];

  if (isLoadingResults) {
    return <Loader text="Loading candidate screening evaluations rankings..." />;
  }

  if (errorResults) {
    return <ErrorState retryAction={fetchResults} description={errorResults} />;
  }

  if (rankings.length === 0) {
    return (
      <EmptyState
        title="No Screening Results Found"
        description="Verify you have uploaded a job description and resume documents, then initiate the screening pipeline."
        action={
          <Button onClick={() => navigate('/upload')} icon="📋">
            Upload Files
          </Button>
        }
      />
    );
  }

  return (
    <div>
      {/* Metrics Row */}
      <div className={styles.grid}>
        <div className={styles.cardMetric}>
          <span className={styles.val}>{rankings.length}</span>
          <span className={styles.lbl}>Evaluated Resumes</span>
        </div>
        <div className={styles.cardMetric}>
          <span className={styles.val}>{stats.avg}%</span>
          <span className={styles.lbl}>Average Alignment</span>
        </div>
        <div className={styles.cardMetric}>
          <span className={styles.val}>{stats.max}%</span>
          <span className={styles.lbl}>Highest Match Score</span>
        </div>
        <div className={styles.cardMetric}>
          <span className={styles.val}>{stats.strongCount}</span>
          <span className={styles.lbl}>Strong Hires Qualified</span>
        </div>
      </div>

      {/* Table Controls (Search, Filters, Downloads) */}
      <div className={styles.controlsRow}>
        <SearchBar value={searchQuery} onChange={setSearchQuery} placeholder="Search candidate by name..." />
        <div className={styles.downloads}>
          <DownloadButton format="csv" />
          <DownloadButton format="json" />
          <DownloadButton format="report" />
        </div>
      </div>

      <FilterPanel
        recommendationFilter={recommendationFilter}
        onRecommendationChange={setRecommendationFilter}
        minScoreFilter={minScoreFilter}
        onMinScoreChange={setMinScoreFilter}
      />

      {/* Main interactive rankings Table */}
      <Table
        columns={columns}
        data={paginatedRankings}
        onRowClick={(row) => navigate(`/results/${row.candidate_id}`)}
        emptyMessage="No candidates matched the selected search or filters criteria."
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setPage}
        startIndex={startIndex}
        endIndex={endIndex}
        totalItems={filteredRankings.length}
      />
    </div>
  );
};

export default Results;
