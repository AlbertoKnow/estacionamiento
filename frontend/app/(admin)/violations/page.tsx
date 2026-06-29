'use client';

import { useState } from 'react';
import ViolationTable from '@/components/admin/ViolationTable';
import ViolationCreateForm from '@/components/admin/ViolationCreateForm';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';

const CREATE_ROLES = ['asistente_operaciones', 'jefe_operaciones', 'director', 'rector'];

export default function ViolationsPage() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const canCreate = user?.rol && CREATE_ROLES.includes(user.rol);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800">Infracciones</h1>
        {canCreate && (
          <Button onClick={() => setOpen(true)} size="sm" className="shrink-0">
            <span className="hidden sm:inline">Nueva infracción</span>
            <span className="sm:hidden">+ Nueva</span>
          </Button>
        )}
      </div>
      <ViolationTable />
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="w-[95vw] max-w-lg">
          <DialogHeader>
            <DialogTitle>Registrar infracción</DialogTitle>
          </DialogHeader>
          <ViolationCreateForm onSuccess={() => setOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
