import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface Vehicle {
  id: number;
  placa: string;
  tipo: string;
  marca: string;
  modelo: string;
  color: string;
}

export function useMyVehicle() {
  return useQuery({
    queryKey: ['my-vehicle'],
    queryFn: () =>
      api.get<Vehicle[]>('/vehicles/my/').then((r) => r.data[0] ?? null),
  });
}

export function useUpsertVehicle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Vehicle>) =>
      data.id
        ? api.patch(`/vehicles/${data.id}/`, data).then((r) => r.data)
        : api.post('/vehicles/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-vehicle'] }),
  });
}
