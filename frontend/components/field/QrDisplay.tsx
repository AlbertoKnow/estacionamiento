'use client';

import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '@/contexts/AuthContext';
import { useMyQrToken } from '@/hooks/useMyQrToken';
import { RefreshCw } from 'lucide-react';

export default function QrDisplay() {
  const { user } = useAuth();
  const { data, isLoading, refetch, isRefetching } = useMyQrToken();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center p-8 text-slate-500">
        No se pudo obtener el código QR.
        <button onClick={() => refetch()} className="block mx-auto mt-2 text-blue-700 underline">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <div className="bg-white p-4 rounded-2xl shadow-md border border-slate-100">
        <QRCodeSVG value={data.token} size={240} level="M" />
      </div>
      <div className="text-center">
        <p className="text-xl font-bold text-slate-800">
          {user?.nombre} {user?.apellido}
        </p>
        <p className="text-sm text-slate-500">{user?.codigo_institucional}</p>
      </div>
      <button
        onClick={() => refetch()}
        disabled={isRefetching}
        className="flex items-center gap-1 text-sm text-blue-700 disabled:opacity-50"
      >
        <RefreshCw size={14} className={isRefetching ? 'animate-spin' : ''} />
        Actualizar QR
      </button>
    </div>
  );
}
