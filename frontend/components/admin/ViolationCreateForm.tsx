'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { useViolationTypes, useCreateViolation } from '@/hooks/useViolations';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

interface SearchedUser {
  id: number;
  codigo_institucional: string;
  nombre: string;
  apellido: string;
}

const NIVEL_LABEL: Record<string, string> = {
  leve: 'Leve',
  grave: 'Grave',
  muy_grave: 'Muy Grave',
};

export default function ViolationCreateForm({ onSuccess }: { onSuccess: () => void }) {
  const { data: types } = useViolationTypes();
  const { mutateAsync, isPending } = useCreateViolation();

  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchedUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<SearchedUser | null>(null);
  const [tipoId, setTipoId] = useState<number | null>(null);
  const [descripcion, setDescripcion] = useState('');
  const [formError, setFormError] = useState('');

  async function handleSearch() {
    if (!query.trim()) return;
    const res = await api.get<SearchedUser[]>(`/users/?search=${query}`);
    setSearchResults(res.data);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');
    if (!tipoId) {
      setFormError('Selecciona un tipo de falta');
      return;
    }
    if (!selectedUser) {
      setFormError('Selecciona un usuario');
      return;
    }
    try {
      await mutateAsync({ user_id: selectedUser.id, tipo_falta_id: tipoId, descripcion });
      toast.success('Infracción registrada');
      onSuccess();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al registrar la infracción';
      toast.error(msg);
    }
  }

  const selectedType = types?.find((t) => t.id === tipoId);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* User search */}
      <div>
        <Label>Usuario</Label>
        <div className="flex gap-2 mt-1">
          <Input
            placeholder="Código institucional o nombre"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleSearch())}
          />
          <Button type="button" variant="outline" onClick={handleSearch}>
            Buscar
          </Button>
        </div>
        {searchResults.length > 0 && !selectedUser && (
          <ul className="mt-1 border rounded-md divide-y text-sm">
            {searchResults.map((u) => (
              <li key={u.id}>
                <button
                  type="button"
                  onClick={() => { setSelectedUser(u); setSearchResults([]); setQuery(''); }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-50"
                >
                  {u.nombre} {u.apellido} · {u.codigo_institucional}
                </button>
              </li>
            ))}
          </ul>
        )}
        {selectedUser && (
          <div className="mt-1 flex items-center gap-2 text-sm bg-blue-50 px-3 py-2 rounded-md">
            <span className="font-medium">{selectedUser.nombre} {selectedUser.apellido}</span>
            <span className="text-slate-400">{selectedUser.codigo_institucional}</span>
            <button
              type="button"
              onClick={() => setSelectedUser(null)}
              className="ml-auto text-xs text-slate-400 hover:text-red-500"
            >
              Cambiar
            </button>
          </div>
        )}
      </div>

      {/* Violation type */}
      <div>
        <Label htmlFor="tipo">Tipo de falta</Label>
        <select
          id="tipo"
          value={tipoId ?? ''}
          onChange={(e) => setTipoId(Number(e.target.value) || null)}
          className="w-full h-10 px-3 border border-input rounded-md text-sm bg-background mt-1"
        >
          <option value="">Seleccionar...</option>
          {types?.map((t) => (
            <option key={t.id} value={t.id}>
              [{NIVEL_LABEL[t.nivel]}] {t.nombre}
            </option>
          ))}
        </select>
      </div>

      {/* Sanction preview */}
      {selectedType && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
          <p className="font-medium text-amber-800">Sanción que se calculará al confirmar:</p>
          <p className="text-amber-700 mt-1">
            Depende del historial previo del usuario en faltas de nivel{' '}
            <Badge variant="outline" className="text-amber-700 border-amber-400">
              {NIVEL_LABEL[selectedType.nivel]}
            </Badge>
          </p>
        </div>
      )}

      {/* Description */}
      <div>
        <Label htmlFor="desc">Descripción (opcional)</Label>
        <Input
          id="desc"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Observaciones adicionales..."
        />
      </div>

      {formError && <p className="text-sm text-destructive">{formError}</p>}

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? 'Registrando...' : 'Registrar infracción'}
      </Button>
    </form>
  );
}
