import { useState, useCallback } from 'react';
import api from '@/lib/api';

export type ScanStatus = 'idle' | 'success' | 'error' | 'offline';

export interface ScanResultData {
  status: ScanStatus;
  nombre?: string;
  placa?: string;
  tipo?: 'entry' | 'exit';
  message?: string;
  timestamp: Date;
}

export function useScan() {
  const [lastResult, setLastResult] = useState<ScanResultData | null>(null);
  const [history, setHistory] = useState<ScanResultData[]>([]);

  const scan = useCallback(async (qr_token: string, tipo: 'entry' | 'exit') => {
    const timestamp = new Date();
    if (!navigator.onLine) {
      const result: ScanResultData = { status: 'offline', tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
    try {
      const endpoint = tipo === 'entry' ? '/access/entry/' : '/access/exit/';
      const res = await api.post<{ usuario: string; placa: string }>(endpoint, { qr_token });
      const result: ScanResultData = {
        status: 'success',
        nombre: res.data.usuario,
        placa: res.data.placa,
        tipo,
        timestamp,
      };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
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
