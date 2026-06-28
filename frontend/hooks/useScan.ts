import { useState, useCallback } from 'react';
import api from '@/lib/api';

export type ScanStatus = 'idle' | 'success' | 'error' | 'offline';

export type ScanResultData =
  | { status: 'success'; tipo: 'entry'; nombre: string; codigo: string; rol: string; espacio: string; timestamp: Date }
  | { status: 'success'; tipo: 'exit'; espacio: string; duracion_minutos: number; timestamp: Date }
  | { status: 'error'; tipo: 'entry' | 'exit'; message: string; timestamp: Date }
  | { status: 'offline'; tipo: 'entry' | 'exit'; timestamp: Date };

export function useScan() {
  const [lastResult, setLastResult] = useState<ScanResultData | null>(null);
  const [history, setHistory] = useState<ScanResultData[]>([]);

  const scan = useCallback(async (token: string, tipo: 'entry' | 'exit') => {
    const timestamp = new Date();
    if (!navigator.onLine) {
      // Persist to IndexedDB for later sync
      const { enqueueScan } = await import('@/lib/offline-queue');
      await enqueueScan({ token, tipo, timestamp: timestamp.toISOString() });
      const result: ScanResultData = { status: 'offline', tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
    try {
      const endpoint = tipo === 'entry' ? '/access/entry/' : '/access/exit/';
      if (tipo === 'entry') {
        const res = await api.post<{
          access_record_id: number;
          session_token: string;
          space: { id: number; numero: string; tipo: string };
          user: { codigo: string; nombre: string; rol: string };
        }>(endpoint, { token });
        const result: ScanResultData = {
          status: 'success',
          tipo: 'entry',
          nombre: res.data.user.nombre,
          codigo: res.data.user.codigo,
          rol: res.data.user.rol,
          espacio: res.data.space.numero,
          timestamp,
        };
        setLastResult(result);
        setHistory((prev) => [result, ...prev].slice(0, 10));
        return result;
      } else {
        const res = await api.post<{
          access_record_id: number;
          space: { id: number; numero: string };
          duracion_minutos: number;
        }>(endpoint, { token });
        const result: ScanResultData = {
          status: 'success',
          tipo: 'exit',
          espacio: res.data.space.numero,
          duracion_minutos: res.data.duracion_minutos,
          timestamp,
        };
        setLastResult(result);
        setHistory((prev) => [result, ...prev].slice(0, 10));
        return result;
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'QR inválido o expirado.';
      const result: ScanResultData = { status: 'error', message: msg, tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
  }, []);

  return { scan, lastResult, history };
}
