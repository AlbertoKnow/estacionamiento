'use client';

import { useOccupancy } from '@/hooks/useOccupancy';
import OccupancyCard from '@/components/admin/OccupancyCard';

export default function DashboardPage() {
  const { data, isLoading, dataUpdatedAt } = useOccupancy();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
        <div className="grid grid-cols-2 gap-4">
          {[0, 1].map((i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const updatedAgo = dataUpdatedAt
    ? Math.round((Date.now() - dataUpdatedAt) / 1000)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Ocupación en tiempo real</h1>
        {updatedAgo !== null && (
          <p className="text-xs text-slate-400">
            Actualizado hace {updatedAgo}s · se actualiza cada 15s
          </p>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data?.lots.map((lot) => (
          <OccupancyCard
            key={lot.id}
            nombre={lot.nombre}
            nivel={lot.nivel}
            total={lot.total}
            libres={lot.libres}
            ocupados={lot.ocupados}
            reservados={lot.reservados}
          />
        ))}
      </div>
    </div>
  );
}
