import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface SpaceCount {
  total: number;
  libres: number;
  ocupados: number;
  reservados: number;
  por_tipo: Record<string, { total: number; libres: number; ocupados: number; reservados: number }>;
}

interface LotData extends SpaceCount {
  id: number;
  nombre: string;
  nivel: string;
}

export interface OccupancyData {
  campus_id: number;
  campus_nombre: string;
  lots: LotData[];
}

export function useOccupancy() {
  const { user } = useAuth();
  const campusId = user?.campus_asignado?.id;

  return useQuery({
    queryKey: ['occupancy', campusId],
    queryFn: () =>
      api.get<OccupancyData>(`/campus/${campusId}/occupancy/`).then((r) => r.data),
    enabled: !!campusId,
    refetchInterval: 15_000,
    staleTime: 10_000,
  });
}
