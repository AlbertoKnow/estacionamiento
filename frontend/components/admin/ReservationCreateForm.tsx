'use client';

import { useState } from 'react';
import { useCreateReservation } from '@/hooks/useReservations';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '@/lib/api';

interface Space {
  id: number;
  codigo: string;
  tipo: string;
  estado: string;
}

export default function ReservationCreateForm({ onSuccess }: { onSuccess: () => void }) {
  const { mutateAsync, isPending } = useCreateReservation();
  const [spaceId, setSpaceId] = useState<number | null>(null);
  const [spaceQuery, setSpaceQuery] = useState('');
  const [spaceResults, setSpaceResults] = useState<Space[]>([]);
  const [inicio, setInicio] = useState('');
  const [fin, setFin] = useState('');
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState('');

  async function searchSpaces() {
    const res = await api.get<{ lots: { spaces: Space[] }[] }>(
      `/spaces/campus/current/occupancy/`
    );
    const all = res.data.lots.flatMap((l) => l.spaces ?? []);
    setSpaceResults(all.filter((s) => s.estado === 'LIBRE'));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (!spaceId) { setError('Selecciona un espacio'); return; }
    if (!inicio || !fin) { setError('Ingresa fecha y hora de inicio y fin'); return; }
    if (!motivo.trim()) { setError('Ingresa el motivo'); return; }
    try {
      await mutateAsync({ space_id: spaceId, inicio, fin, motivo });
      toast.success('Reserva creada');
      onSuccess();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al crear la reserva';
      setError(msg);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label>Espacio</Label>
        <div className="flex gap-2 mt-1">
          <Input
            placeholder="Buscar espacio libre..."
            value={spaceQuery}
            onChange={(e) => setSpaceQuery(e.target.value)}
            readOnly={!!spaceId}
          />
          {!spaceId && (
            <Button type="button" variant="outline" onClick={searchSpaces}>
              Buscar libres
            </Button>
          )}
          {spaceId && (
            <Button type="button" variant="outline" onClick={() => { setSpaceId(null); setSpaceQuery(''); }}>
              Cambiar
            </Button>
          )}
        </div>
        {spaceResults.length > 0 && !spaceId && (
          <ul className="mt-1 border rounded-md divide-y text-sm max-h-40 overflow-y-auto">
            {spaceResults.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => { setSpaceId(s.id); setSpaceQuery(`${s.codigo} (${s.tipo})`); setSpaceResults([]); }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-50"
                >
                  {s.codigo} — {s.tipo}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="inicio">Inicio</Label>
          <Input id="inicio" type="datetime-local" value={inicio} onChange={(e) => setInicio(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="fin">Fin</Label>
          <Input id="fin" type="datetime-local" value={fin} onChange={(e) => setFin(e.target.value)} />
        </div>
      </div>
      <div>
        <Label htmlFor="motivo">Motivo</Label>
        <Input id="motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="Visita directorio, reunión..." />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button type="submit" disabled={isPending} className="w-full">
        {isPending ? 'Creando...' : 'Crear reserva'}
      </Button>
    </form>
  );
}
