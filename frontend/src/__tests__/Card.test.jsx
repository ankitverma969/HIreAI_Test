import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Card } from '../components/Card';

describe('Card Component', () => {
  it('renders children content', () => {
    render(<Card>Hello World</Card>);
    expect(screen.getByText('Hello World')).toBeDefined();
  });

  it('renders title when provided', () => {
    render(<Card title="Card Title">Content</Card>);
    expect(screen.getByText('Card Title')).toBeDefined();
  });

  it('renders footer when provided', () => {
    render(<Card footer={<span>Footer Text</span>}>Content</Card>);
    expect(screen.getByText('Footer Text')).toBeDefined();
  });

  it('renders extra slot when provided', () => {
    render(<Card extra={<button>Action</button>}>Content</Card>);
    expect(screen.getByText('Action')).toBeDefined();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(<Card onClick={handleClick}>Clickable Card</Card>);
    fireEvent.click(screen.getByText('Clickable Card'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not render header when no title or extra', () => {
    const { container } = render(<Card>Only Children</Card>);
    // No h3 should exist
    expect(container.querySelector('h3')).toBeNull();
  });

  it('applies hoverable class when hoverable=true', () => {
    const { container } = render(<Card hoverable>Hoverable</Card>);
    const card = container.firstChild;
    expect(card.className).toContain('hoverable');
  });
});
