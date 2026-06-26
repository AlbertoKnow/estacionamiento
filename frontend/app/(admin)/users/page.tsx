'use client';

import { useState } from 'react';
import { useUsers } from '@/hooks/useUsers';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';

const ESTADO_VARIANT: Record<string, 'default' | 'secondary' | 'destructive'> = {
  ACTIVO: 'default',
  INACTIVO: 'secondary',
  SUSPENDIDO: 'destructive',
};

const ROLES = ['', 'alumno', 'academico', 'administrativo', 'agente_seguridad', 'asistente_operaciones', 'jefe_operaciones', 'jefe_seguridad', 'director', 'rector'];

export default function UsersPage() {
  const [search, setSearch] = useState('');
  const [rol, setRol] = useState('');
  const [estado, setEstado] = useState('');
  const { data, isLoading } = useUsers({ rol, estado, search: search || undefined });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Usuarios</h1>
      <div className="flex flex-wrap gap-3">
        <Input
          className="w-56"
          placeholder="Buscar por nombre o código..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          value={rol}
          onChange={(e) => setRol(e.target.value)}
          className="h-10 px-3 border border-input rounded-md text-sm bg-background"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>{r || 'Todos los roles'}</option>
          ))}
        </select>
        <select
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
          className="h-10 px-3 border border-input rounded-md text-sm bg-background"
        >
          <option value="">Todos los estados</option>
          <option value="ACTIVO">Activo</option>
          <option value="SUSPENDIDO">Suspendido</option>
          <option value="INACTIVO">Inactivo</option>
        </select>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nombre</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Sanciones activas</TableHead>
              <TableHead>Vehículos</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-400 py-8">Cargando...</TableCell>
              </TableRow>
            )}
            {!isLoading && !data?.length && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-400 py-8">No se encontraron usuarios.</TableCell>
              </TableRow>
            )}
            {data?.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="font-mono text-sm">{u.codigo_institucional}</TableCell>
                <TableCell>
                  <p className="font-medium">{u.nombre} {u.apellido}</p>
                  <p className="text-xs text-slate-400">{u.email}</p>
                </TableCell>
                <TableCell>
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                    {u.rol.replace(/_/g, ' ')}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={ESTADO_VARIANT[u.estado] ?? 'secondary'}>{u.estado}</Badge>
                </TableCell>
                <TableCell className="text-center">
                  {u.sanciones_activas > 0 ? (
                    <span className="font-bold text-red-600">{u.sanciones_activas}</span>
                  ) : (
                    <span className="text-slate-400">0</span>
                  )}
                </TableCell>
                <TableCell className="text-center">{u.vehiculos}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
