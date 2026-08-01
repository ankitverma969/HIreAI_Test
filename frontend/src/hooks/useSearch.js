import { useState, useMemo } from 'react';

export const useSearch = (items, searchKeys) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;

    const lowerQuery = searchQuery.toLowerCase().trim();
    return items.filter((item) => {
      return searchKeys.some((key) => {
        const val = item[key];
        if (val === null || val === undefined) return false;
        
        if (Array.isArray(val)) {
          return val.some(subVal => String(subVal).toLowerCase().includes(lowerQuery));
        }
        return String(val).toLowerCase().includes(lowerQuery);
      });
    });
  }, [items, searchKeys, searchQuery]);

  return {
    searchQuery,
    setSearchQuery,
    filteredItems,
  };
};

export default useSearch;
