'use client';

import { use, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useConfirmViolation, useAnnulViolation, Violation } from '@/hooks/useViolations';
import { useAuth } from '@/contexts/AuthContext';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

const CONFIRM_ROLES = ['jefe_operaciones', 'director', 'rector'];

export default function ViolationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { user } = useAuth();
  const [motivo, setMotivo] = useState('');

  const { data: v, isLoading } = useQuery({
    queryKey: ['violation', id],
    queryFn: () => api.get<Violation>(`/violations/${id}/`).then((r) => r.data),
  });

  const { mutateAsync: confirm, isPending: confirming } = useConfirmViolation();
  const { mutateAsync: annul, isPending: annulling } = useAnnulViolation();

  const canManage = user?.rol && CONFIRM_ROLES.includes(user.rol);

  async function handleConfirm() {
    try {
      await confirm(Number(id));
      toast.success('Infracción confirmada y sanción aplicada');
      router.push('/violations');
    } catch {
      toast.error('Error al confirmar la infracción');
    }
  }

  async function handleAnnul() {
    if (!motivo.trim()) { toast.error('Ingresa el motivo de anulación'); return; }
    try {
      await annul({ id: Number(id), motivo });
      toast.success('Infracción anulada');
      router.push('/violations');
    } catch {
      toast.error('Error al anular la infracción');
    }
  }

  if (isLoading) return <div className="text-slate-400">Cargando...</div>;
  if (!v) return <div className="text-slate-400">Infracción no encontrada.</div>;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Infracción #{v.id}</h1>
        <Badge variant={v.estado === 'confirmada' ? 'destructive' : v.estado === 'anulada' ? 'secondary' : 'outline'}>
          {v.estado}
        </Badge>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 text-sm">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-slate-400">Usuario</p>
            <p className="font-medium">{v.user.nombre} {v.user.apellido}</p>
            <p className="text-slate-400">{v.user.codigo_institucional}</p>
          </div>
          <div>
            <p className="text-slate-400">Vehículo</p>
            <p className="font-medium">{v.vehicle?.placa ?? '—'}</p>
          </div>
          <div>
            <p className="text-slate-400">Tipo de falta</p>
            <p className="font-medium">{v.tipo_falta.codigo}</p>
            <Badge variant="outline" className="mt-1">{v.tipo_falta.nivel}</Badge>
          </div>
          <div>
            <p className="text-slate-400">Fecha</p>
            <p className="font-medium">{new Date(v.fecha).toLocaleDateString('es-PE')}</p>
          </div>
        </div>
        {v.descripcion && (
          <div>
            <p className="text-slate-400">Descripción</p>
            <p>{v.descripcion}</p>
          </div>
        )}
        {v.sancion && (
          <div className="bg-red-50 rounded-lg p-3">
            <p className="text-red-700 font-medium">Sanción aplicada: {v.sancion.tipo}</p>
            {v.sancion.fin && (
              <p className="text-red-600 text-xs">
                Hasta {new Date(v.sancion.fin).toLocaleDateString('es-PE')}
              </p>
            )}
          </div>
        )}
      </div>

      {canManage && v.estado === 'pendiente' && (
        <div className="space-y-4">
          <Button onClick={handleConfirm} disabled={confirming} className="w-full">
            {confirming ? 'Confirmando...' : 'Confirmar infracción y aplicar sanción'}
          </Button>
          <div className="space-y-2">
            <Label htmlFor="motivo">Motivo de anulación</Label>
            <Input
              id="motivo"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Explica por qué se anula esta infracción..."
            />
            <Button
              variant="outline"
              onClick={handleAnnul}
              disabled={annulling}
              className="w-full text-red-600 border-red-200 hover:bg-red-50"
            >
              {annulling ? 'Anulando...' : 'Anular infracción'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
