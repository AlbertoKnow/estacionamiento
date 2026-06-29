'use client';

import { useMyViolations } from '@/hooks/useMyViolations';

const NIVEL_CONFIG = {
  leve: { label: 'Leve', bg: 'bg-yellow-100 text-yellow-800' },
  grave: { label: 'Grave', bg: 'bg-orange-100 text-orange-800' },
  muy_grave: { label: 'Muy Grave', bg: 'bg-red-100 text-red-800' },
};

const ESTADO_CONFIG: Record<string, string> = {
  pendiente: 'bg-slate-100 text-slate-600',
  confirmada: 'bg-red-100 text-red-700',
  anulada: 'bg-green-100 text-green-700',
  apelada: 'bg-blue-100 text-blue-700',
};

export default function ViolationList() {
  const { data, isLoading } = useMyViolations();

  if (isLoading) {
    return <div className="p-4 text-slate-500">Cargando...</div>;
  }

  if (!data?.length) {
    return (
      <div className="p-8 text-center text-slate-400">
        No tienes infracciones registradas.
      </div>
    );
  }

  return (
    <ul className="divide-y divide-slate-100">
      {data.map((v) => {
        const nivel = NIVEL_CONFIG[v.tipo_falta.nivel];
        const estadoCls = ESTADO_CONFIG[v.estado] ?? 'bg-slate-100 text-slate-600';
        return (
          <li key={v.id} className="p-4 space-y-1 bg-white">
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${nivel.bg}`}>
                {nivel.label}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${estadoCls}`}>
                {v.estado}
              </span>
            </div>
            <p className="text-sm font-medium text-slate-800">{v.tipo_falta.codigo}</p>
            <p className="text-xs text-slate-500">
              {new Date(v.fecha).toLocaleDateString('es-PE')}
            </p>
            {v.sancion && v.estado === 'confirmada' && (
              <p className="text-xs text-red-600">
                Sanción: {v.sancion.tipo}
                {v.sancion.fin ? ` hasta ${new Date(v.sancion.fin).toLocaleDateString('es-PE')}` : ''}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
