import React from 'react';
import styles from './Tooltip.module.css';

export const Tooltip = ({ children, text }) => {
  if (!text) return <>{children}</>;
  
  return (
    <div className={styles.container}>
      {children}
      <span className={styles.tooltip}>{text}</span>
    </div>
  );
};

export default Tooltip;
