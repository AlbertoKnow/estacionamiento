# Frontend Plan 04: Admin Screens — Reservas, Reportes, Espacios y Usuarios

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the remaining admin screens: reservation management, report downloads (xlsx/pdf), space viewer, and user list.

**Architecture:** All screens under `app/(admin)/`. Reports trigger file downloads via Axios with `responseType: 'blob'`. Reservations include a create modal. Spaces and users are read-heavy with minimal editing.

**Prerequisites:** Plan 01 (foundation) and Plan 03 (admin layout + Sidebar) must be complete.

**Tech Stack:** Next.js 14, TanStack Query v5, Axios blob download, Tailwind CSS, shadcn/ui

## Global Constraints
- All commands run from `frontend/` directory.
- All API calls use `api` from `@/lib/api`.
- TypeScript strict — no `any`.
- Never add `Co-Authored-By: Claude` to git commits.
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/hooks/useReservations.ts` | Create | List, create, cancel reservations |
| `frontend/components/admin/ReservationCreateForm.tsx` | Create | Create reservation modal form |
| `frontend/app/(admin)/reservations/page.tsx` | Create | Reservations list + create button |
| `frontend/lib/download.ts` | Create | Blob download helper |
| `frontend/app/(admin)/reports/page.tsx` | Create | Report download accordions |
| `frontend/app/(admin)/spaces/page.tsx` | Create | Spaces grouped by sótano |
| `frontend/hooks/useSpaces.ts` | Create | Fetch spaces by campus/lot |
| `frontend/app/(admin)/users/page.tsx` | Create | Paginated user list with filters |
| `frontend/hooks/useUsers.ts` | Create | Fetch users with filters |

---

### Task 1: Reservations — list and create

**Files:**
- Create: `frontend/hooks/useReservations.ts`
- Create: `frontend/components/admin/ReservationCreateForm.tsx`
- Create: `frontend/app/(admin)/reservations/page.tsx`

- [ ] **Step 1: Create `hooks/useReservations.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface Reservation {
  id: number;
  space: { id: number; codigo: string; tipo: string };
  reservado_por: { nombre: string; apellido: string };
  beneficiario: { nombre: string; apellido: string } | null;
  campus: { id: number; nombre: string };
  inicio: string;
  fin: string;
  motivo: string;
  estado: 'ACTIVA' | 'CANCELADA' | 'EXPIRADA';
}

export function useReservations() {
  return useQuery({
    queryKey: ['reservations'],
    queryFn: () => api.get<Reservation[]>('/reservations/').then((r) => r.data),
  });
}

export function useCreateReservation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      space_id: number;
      inicio: string;
      fin: string;
      motivo: string;
      beneficiario_id?: number;
    }) => api.post<Reservation>('/reservations/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  });
}

export function useCancelReservation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/reservations/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  });
}
```

- [ ] **Step 2: Create `components/admin/ReservationCreateForm.tsx`**

```typescript
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
```

- [ ] **Step 3: Create `app/(admin)/reservations/page.tsx`**

```typescript
'use client';

import { useState } from 'react';
import { useReservations, useCancelReservation } from '@/hooks/useReservations';
import ReservationCreateForm from '@/components/admin/ReservationCreateForm';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

export default function ReservationsPage() {
  const { data, isLoading } = useReservations();
  const { mutateAsync: cancel } = useCancelReservation();
  const [open, setOpen] = useState(false);

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
        <Button onClick={() => setOpen(true)}>Nueva reserva</Button>
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
```

- [ ] **Step 4: Commit**

```bash
git add frontend/hooks/useReservations.ts frontend/components/admin/ReservationCreateForm.tsx frontend/app/\(admin\)/reservations/page.tsx
git commit -m "feat: add reservations management page with create and cancel"
```

---

### Task 2: Reports — download xlsx/pdf

**Files:**
- Create: `frontend/lib/download.ts`
- Create: `frontend/app/(admin)/reports/page.tsx`

- [ ] **Step 1: Create `lib/download.ts`**

```typescript
import api from './api';

export async function downloadReport(
  url: string,
  params: Record<string, string>,
  filename: string
): Promise<void> {
  const response = await api.get(url, {
    params,
    responseType: 'blob',
  });
  const contentType = response.headers['content-type'] as string;
  const ext = contentType?.includes('pdf') ? 'pdf' : 'xlsx';
  const blob = new Blob([response.data as BlobPart], { type: contentType });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.${ext}`;
  link.click();
  URL.revokeObjectURL(link.href);
}
```

- [ ] **Step 2: Create `app/(admin)/reports/page.tsx`**

```typescript
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

const DIRECTOR_ROLES = ['DIRECTOR', 'RECTOR'];

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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/download.ts frontend/app/\(admin\)/reports/page.tsx
git commit -m "feat: add reports page with xlsx/pdf download for occupancy, violations, users"
```

---

### Task 3: Spaces — view by sótano

**Files:**
- Create: `frontend/hooks/useSpaces.ts`
- Create: `frontend/app/(admin)/spaces/page.tsx`

- [ ] **Step 1: Create `hooks/useSpaces.ts`**

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export interface SpaceItem {
  id: number;
  codigo: string;
  tipo: string;
  estado: string;
  nivel: string;
}

interface LotWithSpaces {
  id: number;
  nombre: string;
  nivel: string;
  spaces: SpaceItem[];
}

export function useSpacesByLot() {
  const { user } = useAuth();
  const campusId = user?.campus_asignado?.id;

  return useQuery({
    queryKey: ['spaces', campusId],
    queryFn: async () => {
      const lotsRes = await api.get<LotWithSpaces[]>(`/spaces/campus/${campusId}/lots/`);
      return lotsRes.data;
    },
    enabled: !!campusId,
  });
}
```

- [ ] **Step 2: Create `app/(admin)/spaces/page.tsx`**

```typescript
'use client';

import { useSpacesByLot } from '@/hooks/useSpaces';
import { Badge } from '@/components/ui/badge';

const ESTADO_CONFIG: Record<string, { label: string; cls: string }> = {
  LIBRE: { label: 'Libre', cls: 'bg-green-100 text-green-700' },
  OCUPADO: { label: 'Ocupado', cls: 'bg-red-100 text-red-700' },
  RESERVADO: { label: 'Reservado', cls: 'bg-blue-100 text-blue-700' },
  MANTENIMIENTO: { label: 'Mantenimiento', cls: 'bg-slate-100 text-slate-600' },
};

export default function SpacesPage() {
  const { data, isLoading } = useSpacesByLot();

  if (isLoading) return <div className="text-slate-400">Cargando espacios...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-800">Espacios de estacionamiento</h1>
      {data?.map((lot) => (
        <div key={lot.id} className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-slate-700">{lot.nombre}</h2>
            <Badge variant="outline">Nivel {lot.nivel}</Badge>
            <span className="text-sm text-slate-400">{lot.spaces?.length ?? 0} espacios</span>
          </div>
          <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
            {lot.spaces?.map((space) => {
              const cfg = ESTADO_CONFIG[space.estado] ?? ESTADO_CONFIG['LIBRE'];
              return (
                <div
                  key={space.id}
                  className={`rounded-lg p-2 text-center text-xs font-medium ${cfg.cls}`}
                  title={`${space.codigo} — ${space.tipo}`}
                >
                  <p className="font-bold">{space.codigo}</p>
                  <p className="opacity-70">{space.tipo.slice(0, 3)}</p>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/hooks/useSpaces.ts frontend/app/\(admin\)/spaces/page.tsx
git commit -m "feat: add spaces view grouped by sótano with occupancy state colors"
```

---

### Task 4: Users — paginated list with filters

**Files:**
- Create: `frontend/hooks/useUsers.ts`
- Create: `frontend/app/(admin)/users/page.tsx`

- [ ] **Step 1: Create `hooks/useUsers.ts`**

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface UserItem {
  id: number;
  codigo_institucional: string;
  nombre: string;
  apellido: string;
  email: string;
  rol: string;
  estado: string;
  sanciones_activas: number;
  vehiculos: number;
}

export function useUsers(filters?: { rol?: string; estado?: string; search?: string }) {
  const params = new URLSearchParams();
  if (filters?.rol) params.set('rol', filters.rol);
  if (filters?.estado) params.set('estado', filters.estado);
  if (filters?.search) params.set('search', filters.search);

  return useQuery({
    queryKey: ['users', filters],
    queryFn: () =>
      api.get<UserItem[]>(`/users/?${params}`).then((r) => r.data),
  });
}
```

- [ ] **Step 2: Create `app/(admin)/users/page.tsx`**

```typescript
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

const ROLES = ['', 'ALUMNO', 'DOCENTE', 'ADMINISTRATIVO', 'AGENTE', 'JEFE_OPERACIONES', 'JEFE_SEGURIDAD', 'DIRECTOR', 'RECTOR'];

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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/hooks/useUsers.ts frontend/app/\(admin\)/users/page.tsx
git commit -m "feat: add users list with role/status filters and sanction indicators"
```

---

## Plan 04 complete

Run full test suite:
```bash
npm run test
```
Expected: All tests from Plans 01–03 still pass.

All admin screens complete: reservations, reports with file download, spaces visual grid, and users list. Plan 05 adds the offline queue, PWA service worker, and E2E tests.
