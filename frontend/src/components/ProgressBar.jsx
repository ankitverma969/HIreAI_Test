import React from 'react';
import styles from './ProgressBar.module.css';

export const ProgressBar = ({ value = 0, label, showDetails = true }) => {
  const roundedValue = Math.min(100, Math.max(0, Math.round(value)));

  return (
    <div className={styles.container}>
      {showDetails && (label || roundedValue !== undefined) && (
        <div className={styles.details}>
          {label && <span className={styles.label}>{label}</span>}
          <span className={styles.value}>{roundedValue}%</span>
        </div>
      )}
      <div className={styles.track}>
        <div 
          className={styles.fill} 
          style={{ width: `${roundedValue}%` }}
        >
          {roundedValue < 100 && roundedValue > 0 && <div className={styles.glow} />}
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
