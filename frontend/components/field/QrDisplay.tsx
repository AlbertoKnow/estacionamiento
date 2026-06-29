'use client';

import Link from 'next/link';
import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '@/contexts/AuthContext';
import { useMyVehicle } from '@/hooks/useMyVehicle';
import { useMyQrToken } from '@/hooks/useMyQrToken';
import { RefreshCw } from 'lucide-react';

export default function QrDisplay() {
  const { user } = useAuth();
  const { data: vehicle, isLoading: vehicleLoading } = useMyVehicle();
  const { data, isLoading: qrLoading, refetch, isRefetching } = useMyQrToken(vehicle?.id);

  if (vehicleLoading || qrLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700" />
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="text-center p-8 space-y-3">
        <p className="text-slate-600 font-medium">No tienes un vehículo registrado</p>
        <p className="text-sm text-slate-400">Necesitas registrar tu vehículo para obtener el código QR de acceso.</p>
        <Link
          href="/my-vehicle"
          className="inline-block mt-2 px-4 py-2 bg-blue-700 text-white text-sm rounded-lg hover:bg-blue-800"
        >
          Registrar vehículo
        </Link>
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
        <QRCodeSVG value={data.token} size={260} level="M" className="w-full h-auto max-w-xs" />
      </div>
      <div className="text-center">
        <p className="text-xl font-bold text-slate-800">
          {user?.nombre} {user?.apellido}
        </p>
        <p className="text-sm text-slate-500">{user?.codigo_institucional}</p>
        <p className="text-xs text-slate-400 mt-1">{vehicle.placa} · {vehicle.tipo}</p>
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
