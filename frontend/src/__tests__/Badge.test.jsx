import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge, RecommendationBadge } from '../components/Badge';

describe('Badge Components', () => {
  it('renders generic badge text', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText('Test Badge')).toBeInTheDocument();
  });

  it('maps strong hire recommendation to success color classes', () => {
    const { container } = render(<RecommendationBadge recommendation="Strong Hire" />);
    expect(screen.getByText('Strong Hire')).toBeInTheDocument();
    expect(container.firstChild).toHaveClass(/success/);
  });

  it('maps reject recommendation to danger color classes', () => {
    const { container } = render(<RecommendationBadge recommendation="Reject" />);
    expect(screen.getByText('Reject')).toBeInTheDocument();
    expect(container.firstChild).toHaveClass(/danger/);
  });

  it('defaults to info variant for unspecified decisions', () => {
    const { container } = render(<RecommendationBadge recommendation="Something Else" />);
    expect(container.firstChild).toHaveClass(/info/);
  });
});
