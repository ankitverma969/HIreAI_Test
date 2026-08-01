import React from 'react';
import styles from './FeedbackComponents.module.css';
import Button from './Button';

export const Spinner = ({ text = 'Loading...' }) => {
  return (
    <div className={styles.spinnerContainer}>
      <div className={styles.spinner} />
      {text && <p className={styles.loadingText}>{text}</p>}
    </div>
  );
};

export const Loader = Spinner;

export const EmptyState = ({
  title = 'No Candidates Scanned Yet',
  description = 'Upload a job description and resumes to begin screening and rank candidates.',
  action,
  icon = '📁',
}) => {
  return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>{icon}</div>
      <h3 className={styles.emptyTitle}>{title}</h3>
      <p className={styles.emptyDesc}>{description}</p>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
};

export const ErrorState = ({
  title = 'Something Went Wrong',
  description = 'We encountered an error while communicating with the screening server. Please verify the backend is online and try again.',
  retryAction,
}) => {
  return (
    <div className={styles.errorState}>
      <div className={styles.errorIcon}>⚠️</div>
      <h3 className={styles.errorTitle}>{title}</h3>
      <p className={styles.errorDesc}>{description}</p>
      {retryAction && (
        <Button onClick={retryAction} variant="secondary" style={{ marginTop: '8px' }}>
          Retry Request
        </Button>
      )}
    </div>
  );
};
export default Spinner;
