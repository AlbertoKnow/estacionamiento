import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface Vehicle {
  id: number;
  placa: string;
  tipo: string;
  marca: string;
  modelo: string;
  color: string;
}

export function useMyVehicle() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['my-vehicle', user?.id],
    queryFn: () =>
      api.get<Vehicle[]>(`/users/${user!.id}/vehicles/`).then((r) => r.data[0] ?? null),
    enabled: !!user?.id,
  });
}

export function useUpsertVehicle() {
  const { user } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Vehicle>) =>
      data.id
        ? api.patch(`/users/${user!.id}/vehicles/${data.id}/`, data).then((r) => r.data)
        : api.post(`/users/${user!.id}/vehicles/`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-vehicle'] }),
  });
}
