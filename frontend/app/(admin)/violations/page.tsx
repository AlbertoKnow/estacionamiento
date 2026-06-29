'use client';

import { useState } from 'react';
import ViolationTable from '@/components/admin/ViolationTable';
import ViolationCreateForm from '@/components/admin/ViolationCreateForm';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';

const CREATE_ROLES = ['asistente_operaciones', 'agente_seguridad', 'jefe_operaciones', 'jefe_seguridad'];

export default function ViolationsPage() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const canCreate = user?.rol && CREATE_ROLES.includes(user.rol);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Infracciones</h1>
        {canCreate && (
          <Button onClick={() => setOpen(true)}>Nueva infracción</Button>
        )}
      </div>
      <ViolationTable />
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Registrar infracción</DialogTitle>
          </DialogHeader>
          <ViolationCreateForm onSuccess={() => setOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
