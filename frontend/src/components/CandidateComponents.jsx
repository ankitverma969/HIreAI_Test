import React from 'react';
import styles from './CandidateComponents.module.css';
import { RecommendationBadge } from './Badge';

export const CandidateScore = ({ score = 0, size = 64 }) => {
  const percentage = `${score}%`;
  
  // Decide score color based on value
  let scoreColor = 'var(--danger)';
  if (score >= 80) {
    scoreColor = 'var(--success)';
  } else if (score >= 60) {
    scoreColor = 'var(--primary-color)';
  } else if (score >= 40) {
    scoreColor = 'var(--warning)';
  }

  const customStyle = {
    '--percentage': percentage,
    '--score-color': scoreColor,
    width: `${size}px`,
    height: `${size}px`
  };

  const innerSize = size - 12;

  return (
    <div className={styles.scoreContainer} style={customStyle}>
      <div className={styles.scoreCircle}>
        <div 
          className={styles.scoreInner}
          style={{ width: `${innerSize}px`, height: `${innerSize}px` }}
        >
          {Math.round(score)}%
        </div>
      </div>
    </div>
  );
};

export const CandidateCard = ({ 
  name, 
  experienceYears, 
  skillsCount = 0, 
  score = 0, 
  recommendation, 
  onClick 
}) => {
  return (
    <div className={styles.candidateCard} onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div className={styles.leftInfo}>
        <h4 className={styles.name}>{name}</h4>
        <div className={styles.details}>
          <span>💼 {experienceYears} yrs experience</span>
          <span style={{ margin: '0 8px', color: 'var(--border-color)' }}>|</span>
          <span>🛠️ {skillsCount} skills matched</span>
        </div>
        <div style={{ marginTop: '6px' }}>
          <RecommendationBadge recommendation={recommendation} />
        </div>
      </div>
      <div className={styles.rightScore}>
        <CandidateScore score={score} size={60} />
        <span className={styles.scoreLabel}>Match</span>
      </div>
    </div>
  );
};
export default CandidateCard;
