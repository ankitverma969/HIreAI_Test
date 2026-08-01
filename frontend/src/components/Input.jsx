import React from 'react';
import styles from './Input.module.css';

export const Input = React.forwardRef(({
  label,
  type = 'text',
  placeholder,
  error,
  disabled = false,
  className = '',
  ...props
}, ref) => {
  return (
    <div className={`${styles.wrapper} ${className}`}>
      {label && <label className={styles.label}>{label}</label>}
      <input
        ref={ref}
        type={type}
        className={`${styles.input} ${error ? styles.errorBorder : ''}`}
        placeholder={placeholder}
        disabled={disabled}
        {...props}
      />
      {error && <span className={styles.errorText}>{error}</span>}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
