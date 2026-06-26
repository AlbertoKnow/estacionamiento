'use client';

import { useState } from 'react';
import { useViolationTypes, useCreateViolation } from '@/hooks/useViolations';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Props {
  onSuccess: () => void;
}

export default function ViolationCreateForm({ onSuccess }: Props) {
  const { data: types, isLoading: typesLoading } = useViolationTypes();
  const { mutate: createViolation, isPending } = useCreateViolation();

  const [userId, setUserId] = useState('');
  const [tipoFaltaId, setTipoFaltaId] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    const uid = parseInt(userId, 10);
    const tid = parseInt(tipoFaltaId, 10);
    if (!uid || !tid) {
      setError('Usuario y tipo de falta son obligatorios.');
      return;
    }
    createViolation(
      { user_id: uid, tipo_falta_id: tid, descripcion: descripcion || undefined },
      {
        onSuccess: () => onSuccess(),
        onError: () => setError('Error al registrar la infracción. Intente de nuevo.'),
      }
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <Label htmlFor="user_id">ID de usuario</Label>
        <Input
          id="user_id"
          type="number"
          placeholder="Ej: 42"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          required
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor="tipo_falta">Tipo de falta</Label>
        <select
          id="tipo_falta"
          value={tipoFaltaId}
          onChange={(e) => setTipoFaltaId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          required
        >
          <option value="">Seleccionar tipo…</option>
          {typesLoading && <option disabled>Cargando…</option>}
          {types?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nombre} ({t.nivel.replace('_', ' ')})
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <Label htmlFor="descripcion">Descripción (opcional)</Label>
        <Input
          id="descripcion"
          placeholder="Observaciones adicionales"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end gap-2 pt-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Guardando…' : 'Registrar infracción'}
        </Button>
      </div>
    </form>
  );
}
