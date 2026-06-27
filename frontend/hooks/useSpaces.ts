import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export interface SpaceItem {
  id: number;
  numero: string;
  tipo: string;
  estado: string;
}

interface Lot {
  id: number;
  nombre: string;
  nivel: number;
}

export interface LotWithSpaces extends Lot {
  spaces: SpaceItem[];
}

export function useSpacesByLot() {
  const { user } = useAuth();
  const campusId = user?.campus_asignado?.id;

  return useQuery({
    queryKey: ['spaces', campusId],
    queryFn: async () => {
      const lotsRes = await api.get<Lot[]>(`/campus/${campusId}/lots/`);
      const lots = lotsRes.data;

      const lotsWithSpaces = await Promise.all(
        lots.map(async (lot) => {
          const spacesRes = await api.get<SpaceItem[]>(
            `/campus/${campusId}/lots/${lot.id}/spaces/`
          );
          return { ...lot, spaces: spacesRes.data };
        })
      );

      return lotsWithSpaces;
    },
    enabled: !!campusId,
  });
}
