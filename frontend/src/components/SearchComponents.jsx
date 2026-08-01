import React from 'react';
import styles from './SearchComponents.module.css';

export const SearchBar = ({ value, onChange, placeholder = 'Search candidates...' }) => {
  return (
    <div className={styles.searchContainer}>
      <span className={styles.searchIcon}>🔍</span>
      <input
        type="text"
        className={styles.searchInput}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Search Candidates"
      />
    </div>
  );
};

export const FilterPanel = ({
  recommendationFilter,
  onRecommendationChange,
  minScoreFilter,
  onMinScoreChange,
  recommendationOptions = ['All Decisions', 'Strong Hire', 'Hire', 'Consider', 'Review', 'Reject'],
}) => {
  return (
    <div className={styles.filterCard}>
      {/* Decision filter */}
      <div className={styles.filterGroup}>
        <span className={styles.filterLabel}>Hiring Recommendation</span>
        <select
          className={styles.filterSelect}
          value={recommendationFilter}
          onChange={(e) => onRecommendationChange(e.target.value)}
          aria-label="Filter by Hiring Recommendation"
        >
          {recommendationOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>

      {/* Min Score filter */}
      <div className={styles.filterGroup}>
        <span className={styles.filterLabel}>Min Overall Score: {minScoreFilter}%</span>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={minScoreFilter}
          onChange={(e) => onMinScoreChange(Number(e.target.value))}
          style={{ width: '180px', accentColor: 'var(--primary-color)' }}
          aria-label="Filter by Minimum Score"
        />
      </div>
    </div>
  );
};
export default SearchBar;
