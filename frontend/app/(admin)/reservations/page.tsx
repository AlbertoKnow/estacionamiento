'use client';

import { useState } from 'react';
import { useReservations, useCancelReservation } from '@/hooks/useReservations';
import ReservationCreateForm from '@/components/admin/ReservationCreateForm';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

export default function ReservationsPage() {
  const { user } = useAuth();
  const { data, isLoading } = useReservations();
  const { mutateAsync: cancel } = useCancelReservation();
  const [open, setOpen] = useState(false);
  const canCreate = user?.rol && ['jefe_operaciones', 'director', 'rector'].includes(user.rol);

  async function handleCancel(id: number) {
    try {
      await cancel(id);
      toast.success('Reserva cancelada');
    } catch {
      toast.error('Error al cancelar');
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Reservas</h1>
        {canCreate && (
          <Button onClick={() => setOpen(true)}>Nueva reserva</Button>
        )}
      </div>

      {isLoading && <p className="text-slate-400">Cargando...</p>}

      <div className="space-y-3">
        {data?.map((r) => (
          <div key={r.id} className="bg-white border border-slate-200 rounded-xl p-4 flex items-start justify-between gap-4">
            <div className="space-y-1 text-sm">
              <div className="flex items-center gap-2">
                <p className="font-semibold text-slate-800">{r.space.codigo} — {r.space.tipo}</p>
                <Badge variant="outline">{r.estado}</Badge>
              </div>
              <p className="text-slate-500">
                {new Date(r.inicio).toLocaleString('es-PE')} → {new Date(r.fin).toLocaleString('es-PE')}
              </p>
              <p className="text-slate-600">{r.motivo}</p>
              {r.beneficiario && (
                <p className="text-slate-400 text-xs">
                  Beneficiario: {r.beneficiario.nombre} {r.beneficiario.apellido}
                </p>
              )}
            </div>
            {r.estado === 'ACTIVA' && (
              <Button
                variant="outline"
                size="sm"
                className="text-red-600 border-red-200 hover:bg-red-50 flex-shrink-0"
                onClick={() => handleCancel(r.id)}
              >
                Cancelar
              </Button>
            )}
          </div>
        ))}
        {!isLoading && !data?.length && (
          <p className="text-slate-400 text-center py-8">No hay reservas activas.</p>
        )}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nueva reserva</DialogTitle>
          </DialogHeader>
          <ReservationCreateForm onSuccess={() => setOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
