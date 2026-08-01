import React from 'react';
import Card from './Card';

export const ChartCard = ({ title, children, className = '', ...props }) => {
  return (
    <Card 
      title={title} 
      className={className} 
      style={{ minHeight: '340px', display: 'flex', flexDirection: 'column' }}
      {...props}
    >
      <div style={{ flex: 1, width: '100%', height: '240px', marginTop: '10px' }}>
        {children}
      </div>
    </Card>
  );
};

export default ChartCard;
