import React, { useState } from 'react';
import Button from './Button';
import { DownloadService } from '../services/downloadService';
import { useNotifications } from '../context/NotificationContext';

export const DownloadButton = ({ format = 'csv', className = '', ...props }) => {
  const [loading, setLoading] = useState(false);
  const { showSuccess, showError } = useNotifications();

  const handleDownload = async () => {
    setLoading(true);
    try {
      if (format === 'csv') {
        await DownloadService.downloadCSV();
      } else if (format === 'json') {
        await DownloadService.downloadJSON();
      } else if (format === 'report') {
        await DownloadService.downloadReport();
      }
      showSuccess(`Successfully downloaded ${format.toUpperCase()} report!`);
    } catch (e) {
      showError(e.message || `Failed to download ${format.toUpperCase()} report.`);
    } finally {
      setLoading(false);
    }
  };

  const getLabel = () => {
    switch (format) {
      case 'csv': return 'Download CSV';
      case 'json': return 'Download JSON';
      case 'report': return 'Download Summary';
      default: return 'Download Report';
    }
  };

  const getIcon = () => {
    switch (format) {
      case 'csv': return '📊';
      case 'json': return '📁';
      case 'report': return '📝';
      default: return '⬇️';
    }
  };

  return (
    <Button
      variant="secondary"
      onClick={handleDownload}
      loading={loading}
      icon={getIcon()}
      className={className}
      {...props}
    >
      {getLabel()}
    </Button>
  );
};

export default DownloadButton;
