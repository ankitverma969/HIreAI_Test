import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, EmptyState } from '../components';

export const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <EmptyState
        title="404 - Page Not Found"
        description="The requested routing endpoint does not exist. Check the URL path spelling or return to the main recruitment dashboard."
        icon="🔍"
        action={
          <Button onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        }
      />
    </div>
  );
};

export default NotFound;
