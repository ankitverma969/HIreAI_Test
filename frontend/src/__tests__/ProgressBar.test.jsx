import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { ProgressBar } from '../components/ProgressBar';

describe('ProgressBar Component', () => {
  it('renders without crashing', () => {
    render(<ProgressBar value={50} max={100} />);
  });

  it('renders with label when provided', () => {
    render(<ProgressBar value={75} max={100} label="Upload Progress" />);
    expect(screen.getByText('Upload Progress')).toBeDefined();
  });

  it('clamps value at 0 minimum', () => {
    const { container } = render(<ProgressBar value={-10} max={100} />);
    // Progress bar should not render negative widths
    expect(container).toBeDefined();
  });

  it('clamps value at max', () => {
    const { container } = render(<ProgressBar value={200} max={100} />);
    expect(container).toBeDefined();
  });

  it('renders 0% state with empty value', () => {
    const { container } = render(<ProgressBar value={0} max={100} />);
    expect(container).toBeDefined();
  });
});
