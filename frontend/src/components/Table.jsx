import React, { useState, useMemo } from 'react';
import styles from './Table.module.css';

export const Table = ({
  columns = [],
  data = [],
  onRowClick,
  emptyMessage = 'No data available.',
  keyField = 'id',
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const handleSort = (key, sortable) => {
    if (!sortable) return;
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;

    const sorted = [...data];
    sorted.sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      // Handle numerical sort
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }

      // Handle string sort
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [data, sortConfig]);

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => {
              const isSorted = sortConfig.key === col.dataIndex;
              const sortIcon = isSorted ? (sortConfig.direction === 'asc' ? '▲' : '▼') : '↕';

              return (
                <th
                  key={col.dataIndex}
                  className={`${styles.th} ${col.sortable ? styles.sortable : ''}`}
                  onClick={() => handleSort(col.dataIndex, col.sortable)}
                  style={{ width: col.width || 'auto' }}
                >
                  {col.title}
                  {col.sortable && <span className={styles.sortIcon}>{sortIcon}</span>}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sortedData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={styles.td} style={{ textAlign: 'center', padding: '32px' }}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedData.map((row, idx) => (
              <tr
                key={row[keyField] || idx}
                className={`${styles.tr} ${onRowClick ? styles.clickable : ''}`}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {columns.map((col) => (
                  <td key={col.dataIndex} className={styles.td}>
                    {col.render ? col.render(row[col.dataIndex], row, idx) : row[col.dataIndex]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export const Pagination = ({
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  startIndex = 0,
  endIndex = 0,
  totalItems = 0,
}) => {
  const pageNumbers = useMemo(() => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  }, [currentPage, totalPages]);

  return (
    <div className={styles.paginationContainer}>
      <div className={styles.paginationInfo}>
        Showing <span style={{ fontWeight: 600 }}>{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
        <span style={{ fontWeight: 600 }}>{endIndex}</span> of{' '}
        <span style={{ fontWeight: 600 }}>{totalItems}</span> candidates
      </div>

      <div className={styles.paginationControls}>
        <button
          className={styles.pageBtn}
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          type="button"
          aria-label="Previous Page"
        >
          ‹
        </button>
        {pageNumbers.map((page) => (
          <button
            key={page}
            className={`${styles.pageBtn} ${currentPage === page ? styles.activePage : ''}`}
            onClick={() => onPageChange(page)}
            type="button"
            aria-label={`Go to page ${page}`}
          >
            {page}
          </button>
        ))}
        <button
          className={styles.pageBtn}
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          type="button"
          aria-label="Next Page"
        >
          ›
        </button>
      </div>
    </div>
  );
};

export default Table;
