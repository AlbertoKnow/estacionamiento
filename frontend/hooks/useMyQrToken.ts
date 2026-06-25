import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface QrTokenResponse {
  qr_token: string;
  expires_at: string;
}

export function useMyQrToken() {
  return useQuery({
    queryKey: ['my-qr-token'],
    queryFn: () => api.get<QrTokenResponse>('/auth/qr-token/').then((r) => r.data),
    staleTime: 1000 * 60 * 4,
    refetchInterval: 1000 * 60 * 4,
  });
}
