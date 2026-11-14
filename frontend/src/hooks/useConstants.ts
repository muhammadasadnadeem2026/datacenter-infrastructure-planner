import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

const forever = { staleTime: Infinity, gcTime: Infinity } as const;

export const useMeta = () => useQuery({ queryKey: ['meta'], queryFn: api.meta, ...forever });
export const usePresets = () => useQuery({ queryKey: ['presets'], queryFn: api.presets, ...forever });
export const useReceptacles = () =>
  useQuery({ queryKey: ['receptacles'], queryFn: api.receptacles, ...forever });
export const useReferences = () =>
  useQuery({ queryKey: ['references'], queryFn: api.references, ...forever });
export const useCoolingClasses = () =>
  useQuery({ queryKey: ['cooling-classes'], queryFn: api.coolingClasses, ...forever });
export const useVoltageLevels = () =>
  useQuery({ queryKey: ['voltage-levels'], queryFn: api.voltageLevels, ...forever });
export const useAiRacks = () => useQuery({ queryKey: ['ai-racks'], queryFn: api.aiRacks, ...forever });
export const useConversions = () =>
  useQuery({ queryKey: ['conversions'], queryFn: api.conversions, ...forever });
