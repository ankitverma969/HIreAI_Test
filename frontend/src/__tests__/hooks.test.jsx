import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePagination } from '../hooks/usePagination';
import { useSearch } from '../hooks/useSearch';
import { useDebounce } from '../hooks/useDebounce';

describe('Custom React Hooks', () => {
  describe('usePagination Hook', () => {
    it('calculates correct indexes and page boundaries', () => {
      const { result } = renderHook(() => usePagination(25, 10));
      
      expect(result.current.currentPage).toBe(1);
      expect(result.current.totalPages).toBe(3);
      expect(result.current.startIndex).toBe(0);
      expect(result.current.endIndex).toBe(10);
      
      act(() => {
        result.current.setPage(2);
      });
      
      expect(result.current.currentPage).toBe(2);
      expect(result.current.startIndex).toBe(10);
      expect(result.current.endIndex).toBe(20);
    });
  });

  describe('useSearch Hook', () => {
    it('filters items correctly based on keyword search query', () => {
      const mockData = [
        { id: 1, name: 'Alice Smith', role: 'Dev' },
        { id: 2, name: 'Bob Johnson', role: 'Designer' },
        { id: 3, name: 'Charlie Brown', role: 'Manager' }
      ];
      
      const { result } = renderHook(() => useSearch(mockData, ['name', 'role']));
      
      expect(result.current.filteredItems).toHaveLength(3);
      
      act(() => {
        result.current.setSearchQuery('designer');
      });
      
      expect(result.current.filteredItems).toHaveLength(1);
      expect(result.current.filteredItems[0].name).toBe('Bob Johnson');
    });
  });

  describe('useDebounce Hook', () => {
    it('delays returning value updates until timing threshold passes', () => {
      vi.useFakeTimers();
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      );

      expect(result.current).toBe('initial');

      // Update value
      rerender({ value: 'updated' });
      expect(result.current).toBe('initial'); // unchanged initially

      // Fast forward time
      act(() => {
        vi.advanceTimersByTime(500);
      });
      expect(result.current).toBe('updated');

      vi.useRealTimers();
    });
  });
});
