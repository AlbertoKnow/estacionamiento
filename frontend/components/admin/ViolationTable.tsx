'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useViolations } from '@/hooks/useViolations';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

const NIVEL_VARIANT: Record<string, 'default' | 'secondary' | 'destructive'> = {
  leve: 'secondary',
  grave: 'default',
  muy_grave: 'destructive',
};

const ESTADO_VARIANT: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  pendiente: 'outline',
  confirmada: 'destructive',
  anulada: 'secondary',
  apelada: 'secondary',
};

export default function ViolationTable() {
  const [estado, setEstado] = useState<string>('');
  const { data, isLoading } = useViolations(estado ? { estado } : undefined);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {['', 'pendiente', 'confirmada', 'anulada'].map((s) => (
          <button
            key={s}
            onClick={() => setEstado(s)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              estado === s ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-600'
            }`}
          >
            {s || 'Todas'}
          </button>
        ))}
      </div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Usuario</TableHead>
              <TableHead>Placa</TableHead>
              <TableHead>Tipo de falta</TableHead>
              <TableHead>Nivel</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-slate-400 py-8">
                  Cargando...
                </TableCell>
              </TableRow>
            )}
            {!isLoading && !data?.length && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-slate-400 py-8">
                  No hay infracciones con el filtro seleccionado.
                </TableCell>
              </TableRow>
            )}
            {data?.map((v) => (
              <TableRow key={v.id}>
                <TableCell>
                  <p className="font-medium text-slate-800">
                    {v.user.nombre} {v.user.apellido}
                  </p>
                  <p className="text-xs text-slate-400">{v.user.codigo_institucional}</p>
                </TableCell>
                <TableCell>{v.vehicle?.placa ?? '—'}</TableCell>
                <TableCell className="max-w-xs truncate">{v.tipo_falta.codigo}</TableCell>
                <TableCell>
                  <Badge variant={NIVEL_VARIANT[v.tipo_falta.nivel]}>
                    {v.tipo_falta.nivel.replace('_', ' ')}
                  </Badge>
                </TableCell>
                <TableCell>
                  {new Date(v.fecha).toLocaleDateString('es-PE')}
                </TableCell>
                <TableCell>
                  <Badge variant={ESTADO_VARIANT[v.estado]}>{v.estado}</Badge>
                </TableCell>
                <TableCell>
                  <Link
                    href={`/violations/${v.id}`}
                    className="text-sm text-blue-700 hover:underline"
                  >
                    Ver
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
