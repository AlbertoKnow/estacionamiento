import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface ViolationItem {
  id: number;
  tipo_falta: { codigo: string; descripcion: string; nivel: 'leve' | 'grave' | 'muy_grave' };
  fecha: string;
  estado: 'pendiente' | 'confirmada' | 'anulada' | 'apelada';
  descripcion: string;
  sancion?: { tipo: string; inicio: string; fin: string | null };
}

export function useMyViolations() {
  return useQuery({
    queryKey: ['my-violations'],
    queryFn: () => api.get<ViolationItem[]>('/violations/my/').then((r) => r.data),
  });
}
