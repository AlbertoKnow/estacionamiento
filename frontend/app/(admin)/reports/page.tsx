'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { downloadReport } from '@/lib/download';
import { toast } from 'sonner';

type Format = 'xlsx' | 'pdf';

function ReportSection({
  title,
  url,
  filename,
  showDates = true,
  campusId,
}: {
  title: string;
  url: string;
  filename: string;
  showDates?: boolean;
  campusId: number | null;
}) {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [fmt, setFmt] = useState<Format>('xlsx');
  const [loading, setLoading] = useState(false);

  async function handle() {
    if (!campusId) { toast.error('No tienes campus asignado'); return; }
    if (showDates && (!dateFrom || !dateTo)) { toast.error('Selecciona el rango de fechas'); return; }
    setLoading(true);
    try {
      const params: Record<string, string> = { format: fmt, campus_id: String(campusId) };
      if (showDates) { params.date_from = dateFrom; params.date_to = dateTo; }
      await downloadReport(url, params, filename);
      toast.success('Reporte descargado');
    } catch {
      toast.error('Error al generar el reporte');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
      <h2 className="font-semibold text-slate-800">{title}</h2>
      {showDates && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor={`from-${filename}`}>Desde</Label>
            <Input id={`from-${filename}`} type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div>
            <Label htmlFor={`to-${filename}`}>Hasta</Label>
            <Input id={`to-${filename}`} type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
        </div>
      )}
      <div className="flex items-center gap-3">
        <div className="flex gap-2">
          {(['xlsx', 'pdf'] as Format[]).map((f) => (
            <button
              key={f}
              onClick={() => setFmt(f)}
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                fmt === f ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
        <Button onClick={handle} disabled={loading} size="sm">
          {loading ? 'Generando...' : 'Descargar'}
        </Button>
      </div>
    </div>
  );
}

const DIRECTOR_ROLES = ['director', 'rector'];

export default function ReportsPage() {
  const { user } = useAuth();
  const campusId = user?.campus_asignado?.id ?? null;
  const isDirector = user?.rol && DIRECTOR_ROLES.includes(user.rol);

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-800">Reportes</h1>
      <ReportSection
        title="Reporte de Ocupación"
        url="/reports/occupancy/"
        filename="reporte_ocupacion"
        campusId={campusId}
      />
      <ReportSection
        title="Reporte de Infracciones"
        url="/reports/violations/"
        filename="reporte_infracciones"
        campusId={campusId}
      />
      {isDirector && (
        <ReportSection
          title="Reporte de Usuarios (HCM)"
          url="/reports/users/"
          filename="reporte_usuarios"
          showDates={false}
          campusId={campusId}
        />
      )}
    </div>
  );
}
