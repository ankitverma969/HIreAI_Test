import React from 'react';
import styles from './Badge.module.css';

export const Badge = ({ children, variant = 'info', className = '' }) => {
  return (
    <span className={`${styles.badge} ${styles[variant]} ${className}`}>
      {children}
    </span>
  );
};

export const RecommendationBadge = ({ recommendation }) => {
  const rec = (recommendation || '').toLowerCase().trim();
  let variant = 'info';

  if (rec === 'strong hire') {
    variant = 'success';
  } else if (rec === 'hire') {
    variant = 'info';
  } else if (rec === 'consider' || rec === 'review') {
    variant = 'warning';
  } else if (rec === 'reject') {
    variant = 'danger';
  }

  return (
    <Badge variant={variant}>
      {recommendation || 'Consider'}
    </Badge>
  );
};

export const SkillBadge = ({ skill, matched = true, missing = false }) => {
  let styleClass = styles.skillBadge;
  if (matched) styleClass += ` ${styles.matched}`;
  if (missing) styleClass += ` ${styles.missing}`;

  return (
    <span className={styleClass}>
      {matched ? '✓' : '✗'} {skill}
    </span>
  );
};

export default Badge;
