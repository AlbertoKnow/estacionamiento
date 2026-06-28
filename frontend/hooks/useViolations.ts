import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface ViolationType {
  id: number;
  codigo: string;
  nivel: 'leve' | 'grave' | 'muy_grave';
  descripcion: string;
}

export interface Violation {
  id: number;
  user: { id: number; nombre: string; apellido: string; codigo_institucional: string };
  vehicle: { placa: string } | null;
  tipo_falta: ViolationType;
  estado: 'pendiente' | 'confirmada' | 'anulada' | 'apelada';
  fecha: string;
  descripcion: string;
  sancion_propuesta?: { tipo: string; duracion_meses: number | null };
  sancion?: { tipo: string; inicio: string; fin: string | null };
}

export function useViolations(filters?: { estado?: string }) {
  const params = new URLSearchParams();
  if (filters?.estado) params.set('estado', filters.estado);
  return useQuery({
    queryKey: ['violations', filters],
    queryFn: () =>
      api.get<Violation[]>(`/violations/?${params}`).then((r) => r.data),
  });
}

export function useViolationTypes() {
  return useQuery({
    queryKey: ['violation-types'],
    queryFn: () => api.get<ViolationType[]>('/violations/types/').then((r) => r.data),
    staleTime: Infinity,
  });
}

export function useCreateViolation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { user_id: number; tipo_falta_id: number; descripcion?: string }) =>
      api.post<Violation>('/violations/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['violations'] }),
  });
}

export function useConfirmViolation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<Violation>(`/violations/${id}/confirm/`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['violations'] }),
  });
}

export function useAnnulViolation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) =>
      api.post<Violation>(`/violations/${id}/annul/`, { motivo }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['violations'] }),
  });
}
