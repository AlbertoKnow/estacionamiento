interface LotCardProps {
  nombre: string;
  nivel: string;
  total: number;
  libres: number;
  ocupados: number;
  reservados: number;
}

export default function OccupancyCard({ nombre, nivel, total, libres, ocupados, reservados }: LotCardProps) {
  const pct = total > 0 ? Math.round((ocupados / total) * 100) : 0;
  const barColor = pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-green-500';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
      <div>
        <p className="font-bold text-slate-800 text-lg">{nombre}</p>
        <p className="text-sm text-slate-500">Nivel {nivel}</p>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-600">{ocupados} / {total} ocupados</span>
          <span className="font-semibold text-slate-800">{pct}%</span>
        </div>
        <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="bg-green-50 rounded-lg p-2">
          <p className="font-bold text-green-700 text-lg">{libres}</p>
          <p className="text-green-600">Libres</p>
        </div>
        <div className="bg-red-50 rounded-lg p-2">
          <p className="font-bold text-red-700 text-lg">{ocupados}</p>
          <p className="text-red-600">Ocupados</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-2">
          <p className="font-bold text-blue-700 text-lg">{reservados}</p>
          <p className="text-blue-600">Reservados</p>
        </div>
      </div>
    </div>
  );
}
