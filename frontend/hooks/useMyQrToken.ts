import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface QrTokenResponse {
  token: string;
  expires_in: number;
}

export function useMyQrToken() {
  return useQuery({
    queryKey: ['my-qr-token'],
    queryFn: () => api.get<QrTokenResponse>('/access/qr/entry/').then((r) => r.data),
    staleTime: 1000 * 60 * 4,
    refetchInterval: 1000 * 60 * 4,
  });
}
