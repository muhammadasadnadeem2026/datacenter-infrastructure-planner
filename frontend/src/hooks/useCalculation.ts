import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { useProjectStore } from '../stores/projectStore';
import type { FullResponse, ToolResponse } from '../types/api';
import { useDebouncedValue } from './useDebouncedValue';

/**
 * Debounce a request body by its serialized form, so a new-but-equal object does not
 * restart the timer, and typing does not flood the API.
 */
function useDebouncedBody(body: unknown | null): string | null {
  const debounceMs = useProjectStore((s) => s.settings.debounceMs);
  const key = body === null || body === undefined ? null : JSON.stringify(body);
  return useDebouncedValue(key, debounceMs);
}

/** Authoritative full-project calculation from the backend engine. */
export function useFullCalculation(inputs: unknown | null) {
  const key = useDebouncedBody(inputs);
  return useQuery<FullResponse>({
    queryKey: ['calc', 'full', key],
    queryFn: () => api.calculateFull(JSON.parse(key as string)),
    enabled: key !== null,
    placeholderData: keepPreviousData,
    staleTime: Infinity,
    retry: false,
  });
}

/** Single-module tool calculation. */
export function useToolCalculation<T = ToolResponse>(endpoint: string, body: unknown | null) {
  const key = useDebouncedBody(body);
  return useQuery<T>({
    queryKey: ['calc', endpoint, key],
    queryFn: () => api.calculateTool<T>(endpoint, JSON.parse(key as string)),
    enabled: key !== null,
    placeholderData: keepPreviousData,
    staleTime: Infinity,
    retry: false,
  });
}
