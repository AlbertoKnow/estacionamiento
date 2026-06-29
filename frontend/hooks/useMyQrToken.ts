import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface QrTokenResponse {
  token: string;
  expires_in: number;
}

export function useMyQrToken(vehicleId: number | undefined) {
  return useQuery({
    queryKey: ['my-qr-token', vehicleId],
    queryFn: () =>
      api.post<QrTokenResponse>('/access/qr/entry/', { vehicle_id: vehicleId })
        .then((r) => r.data),
    staleTime: 1000 * 60 * 4,
    refetchInterval: 1000 * 60 * 4,
    enabled: !!vehicleId,
  });
}
