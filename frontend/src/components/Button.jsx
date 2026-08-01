import React, { useState, useEffect } from 'react';
import styles from './Button.module.css';
import { useNotifications } from '../context/NotificationContext';

export const Button = ({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  disabled = false,
  loading = false,
  icon,
  className = '',
  actionKey = null,
  successMessage = null,
  errorMessage = null,
  infoMessage = null,
  ...props
}) => {
  const { showSuccess, showError, showInfo } = useNotifications();
  const [internalLoading, setInternalLoading] = useState(false);
  const [lastStatus, setLastStatus] = useState(null);

  const isLoading = loading || internalLoading;

  // derive an action key for storing last status
  const key = actionKey || (typeof children === 'string' ? children.trim() : null);

  useEffect(() => {
    try {
      if (key) {
        const map = JSON.parse(sessionStorage.getItem('buttonLastStatus') || '{}');
        setLastStatus(map[key] || null);
      }
    } catch (e) {
      // ignore
    }
  }, [key]);

  const persistStatus = (statusObj) => {
    try {
      const map = JSON.parse(sessionStorage.getItem('buttonLastStatus') || '{}');
      if (key) {
        map[key] = statusObj;
        sessionStorage.setItem('buttonLastStatus', JSON.stringify(map));
        setLastStatus(statusObj);
      }
    } catch (e) {
      // ignore
    }
  };

  const handleClick = async (e) => {
    if (!onClick) return;

    try {
      const result = onClick(e);
      // If the handler returned a promise, handle loading and notifications automatically
      if (result && typeof result.then === 'function') {
        setInternalLoading(true);
        if (infoMessage) showInfo(infoMessage);
        else showInfo('Processing...');
        try {
          const res = await result;
          const msg = (res && res.message) || successMessage || 'Completed successfully.';
          showSuccess(msg);
          persistStatus({ status: 'success', message: msg, timestamp: Date.now() });
          return res;
        } catch (err) {
          const text = (err && err.message) || errorMessage || 'Operation failed.';
          showError(text);
          persistStatus({ status: 'error', message: text, timestamp: Date.now() });
          throw err;
        } finally {
          setInternalLoading(false);
        }
      }
      // synchronous handler
      return result;
    } catch (err) {
      // if onClick threw synchronously
      const text = (err && err.message) || errorMessage || 'Operation failed.';
      showError(text);
      persistStatus({ status: 'error', message: text, timestamp: Date.now() });
      throw err;
    }
  };

  return (
    <button
      type={type}
      className={`${styles.btn} ${styles[variant]} ${className}`}
      disabled={disabled || isLoading}
      onClick={handleClick}
      {...props}
    >
      {isLoading ? (
        <span className={styles.spinner} />
      ) : (
        <>
          {icon && <span className={styles.icon}>{icon}</span>}
          {children}
        </>
      )}

      {/* status badge */}
      {lastStatus && (
        <span
          className={`${styles.statusBadge} ${
            lastStatus.status === 'success' ? styles.statusSuccess : styles.statusError
          }`}
          title={`${lastStatus.status.toUpperCase()}: ${lastStatus.message || ''}`}
        />
      )}
    </button>
  );
};

export default Button;
