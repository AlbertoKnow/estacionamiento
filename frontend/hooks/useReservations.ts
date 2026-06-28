import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface Reservation {
  id: number;
  space: { id: number; codigo: string; tipo: string };
  reservado_por: { nombre: string; apellido: string };
  beneficiario: { nombre: string; apellido: string } | null;
  campus: { id: number; nombre: string };
  inicio: string;
  fin: string;
  motivo: string;
  estado: 'activa' | 'cancelada' | 'vencida';
}

export function useReservations() {
  return useQuery({
    queryKey: ['reservations'],
    queryFn: () => api.get<Reservation[]>('/reservations/').then((r) => r.data),
  });
}

export function useCreateReservation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      space_id: number;
      inicio: string;
      fin: string;
      motivo: string;
      beneficiario_id?: number;
    }) => api.post<Reservation>('/reservations/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  });
}

export function useCancelReservation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/reservations/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  });
}
