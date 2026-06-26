import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface UserItem {
  id: number;
  codigo_institucional: string;
  nombre: string;
  apellido: string;
  email: string;
  rol: string;
  estado: string;
  sanciones_activas: number;
  vehiculos: number;
}

export function useUsers(filters?: { rol?: string; estado?: string; search?: string }) {
  const params = new URLSearchParams();
  if (filters?.rol) params.set('rol', filters.rol);
  if (filters?.estado) params.set('estado', filters.estado);
  if (filters?.search) params.set('search', filters.search);

  return useQuery({
    queryKey: ['users', filters],
    queryFn: () =>
      api.get<UserItem[]>(`/users/?${params}`).then((r) => r.data),
  });
}
