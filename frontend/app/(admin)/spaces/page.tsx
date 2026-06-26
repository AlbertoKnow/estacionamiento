'use client';

import { useSpacesByLot } from '@/hooks/useSpaces';
import { Badge } from '@/components/ui/badge';

const ESTADO_CONFIG: Record<string, { label: string; cls: string }> = {
  LIBRE: { label: 'Libre', cls: 'bg-green-100 text-green-700' },
  OCUPADO: { label: 'Ocupado', cls: 'bg-red-100 text-red-700' },
  RESERVADO: { label: 'Reservado', cls: 'bg-blue-100 text-blue-700' },
  MANTENIMIENTO: { label: 'Mantenimiento', cls: 'bg-slate-100 text-slate-600' },
};

export default function SpacesPage() {
  const { data, isLoading } = useSpacesByLot();

  if (isLoading) return <div className="text-slate-400">Cargando espacios...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-800">Espacios de estacionamiento</h1>
      {data?.map((lot) => (
        <div key={lot.id} className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-slate-700">{lot.nombre}</h2>
            <Badge variant="outline">Nivel {lot.nivel}</Badge>
            <span className="text-sm text-slate-400">{lot.spaces?.length ?? 0} espacios</span>
          </div>
          <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
            {lot.spaces?.map((space) => {
              const cfg = ESTADO_CONFIG[space.estado] ?? ESTADO_CONFIG['LIBRE'];
              return (
                <div
                  key={space.id}
                  className={`rounded-lg p-2 text-center text-xs font-medium ${cfg.cls}`}
                  title={`${space.codigo} — ${space.tipo}`}
                >
                  <p className="font-bold">{space.codigo}</p>
                  <p className="opacity-70">{space.tipo.slice(0, 3)}</p>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
