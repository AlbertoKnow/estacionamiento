import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export interface SpaceItem {
  id: number;
  codigo: string;
  tipo: string;
  estado: string;
  nivel: string;
}

interface LotWithSpaces {
  id: number;
  nombre: string;
  nivel: string;
  spaces: SpaceItem[];
}

export function useSpacesByLot() {
  const { user } = useAuth();
  const campusId = user?.campus_asignado?.id;

  return useQuery({
    queryKey: ['spaces', campusId],
    queryFn: async () => {
      const lotsRes = await api.get<LotWithSpaces[]>(`/spaces/campus/${campusId}/lots/`);
      return lotsRes.data;
    },
    enabled: !!campusId,
  });
}
