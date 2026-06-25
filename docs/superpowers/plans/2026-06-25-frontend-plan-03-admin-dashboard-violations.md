# Frontend Plan 03: Admin Screens — Dashboard y Violaciones

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the admin Sidebar, the real-time occupancy dashboard (polling 15s), and the full violations management flow (list, detail, create, confirm, annul).

**Architecture:** Screens under `app/(admin)/`. The Sidebar replaces the layout skeleton from Plan 01. Occupancy uses TanStack Query with `refetchInterval: 15000`. Violations list uses server-side data. The create form calls `GET /violations/types/` to populate the dropdown and shows the sanction proposal from the backend before confirming.

**Prerequisites:** Plan 01 complete (auth, API client, admin layout skeleton).

**Tech Stack:** Next.js 14, TanStack Query v5, Axios, Tailwind CSS, shadcn/ui (badge, dialog, table, tabs), Vitest, React Testing Library

## Global Constraints
- All commands run from `frontend/` directory.
- All API calls use `api` from `@/lib/api`.
- TypeScript strict — no `any`.
- Never add `Co-Authored-By: Claude` to git commits.
- Desktop-first: admin screens designed for 1024px+ viewport.
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/components/admin/Sidebar.tsx` | Create | Navigation sidebar with role-filtered links |
| `frontend/app/(admin)/layout.tsx` | Modify | Replace skeleton with real Sidebar |
| `frontend/hooks/useOccupancy.ts` | Create | Polling occupancy query |
| `frontend/components/admin/OccupancyCard.tsx` | Create | Sótano card with progress bar |
| `frontend/app/(admin)/dashboard/page.tsx` | Modify | Replace placeholder with real dashboard |
| `frontend/hooks/useViolations.ts` | Create | List, create, confirm, annul mutations |
| `frontend/components/admin/ViolationTable.tsx` | Create | Filterable violations table |
| `frontend/components/admin/ViolationCreateForm.tsx` | Create | Create violation + sanction proposal |
| `frontend/components/admin/ViolationCreateForm.test.tsx` | Create | RTL tests |
| `frontend/app/(admin)/violations/page.tsx` | Modify | Violations list + create button |
| `frontend/app/(admin)/violations/[id]/page.tsx` | Create | Violation detail + confirm/annul |

---

### Task 1: Sidebar and admin layout

**Files:**
- Create: `frontend/components/admin/Sidebar.tsx`
- Modify: `frontend/app/(admin)/layout.tsx`

- [ ] **Step 1: Install shadcn badge component**

```bash
npx shadcn-ui@latest add badge
```

- [ ] **Step 2: Create `components/admin/Sidebar.tsx`**

```typescript
'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard,
  AlertTriangle,
  CalendarClock,
  FileBarChart,
  ParkingSquare,
  Users,
  LogOut,
} from 'lucide-react';
import { toast } from 'sonner';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['JEFE_OPERACIONES', 'JEFE_SEGURIDAD', 'DIRECTOR', 'RECTOR'] },
  { href: '/violations', label: 'Infracciones', icon: AlertTriangle, roles: ['AGENTE', 'JEFE_OPERACIONES', 'JEFE_SEGURIDAD', 'DIRECTOR', 'RECTOR'] },
  { href: '/reservations', label: 'Reservas', icon: CalendarClock, roles: ['JEFE_OPERACIONES', 'DIRECTOR', 'RECTOR'] },
  { href: '/reports', label: 'Reportes', icon: FileBarChart, roles: ['JEFE_SEGURIDAD', 'JEFE_OPERACIONES', 'DIRECTOR', 'RECTOR'] },
  { href: '/spaces', label: 'Espacios', icon: ParkingSquare, roles: ['DIRECTOR', 'RECTOR'] },
  { href: '/users', label: 'Usuarios', icon: Users, roles: ['DIRECTOR', 'RECTOR'] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  const visibleItems = NAV_ITEMS.filter(
    (item) => user?.rol && item.roles.includes(user.rol)
  );

  async function handleLogout() {
    await logout();
    toast.success('Sesión cerrada');
    router.push('/login');
  }

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-full">
      <div className="p-5 border-b border-slate-100">
        <p className="font-bold text-blue-800 text-lg">UTP Parking</p>
        <p className="text-xs text-slate-400">Arequipa — Sótano 2 y 3</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {visibleItems.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-50 text-blue-800'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-100">
        <p className="text-xs font-semibold text-slate-700 truncate">
          {user?.nombre} {user?.apellido}
        </p>
        <p className="text-xs text-slate-400 truncate">{user?.rol?.replace('_', ' ')}</p>
        <button
          onClick={handleLogout}
          className="mt-3 flex items-center gap-2 text-xs text-slate-500 hover:text-red-600 transition-colors"
        >
          <LogOut size={14} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 3: Update `app/(admin)/layout.tsx`**

```typescript
import Sidebar from '@/components/admin/Sidebar';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/admin/Sidebar.tsx frontend/app/\(admin\)/layout.tsx
git commit -m "feat: add admin sidebar with role-filtered navigation"
```

---

### Task 2: Dashboard — real-time occupancy

**Files:**
- Create: `frontend/hooks/useOccupancy.ts`
- Create: `frontend/components/admin/OccupancyCard.tsx`
- Modify: `frontend/app/(admin)/dashboard/page.tsx`

- [ ] **Step 1: Create `hooks/useOccupancy.ts`**

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface SpaceCount {
  total: number;
  libres: number;
  ocupados: number;
  reservados: number;
  por_tipo: Record<string, { total: number; libres: number; ocupados: number; reservados: number }>;
}

interface LotData extends SpaceCount {
  id: number;
  nombre: string;
  nivel: string;
}

export interface OccupancyData {
  campus_id: number;
  campus_nombre: string;
  lots: LotData[];
}

export function useOccupancy() {
  const { user } = useAuth();
  const campusId = user?.campus_asignado?.id;

  return useQuery({
    queryKey: ['occupancy', campusId],
    queryFn: () =>
      api.get<OccupancyData>(`/spaces/campus/${campusId}/occupancy/`).then((r) => r.data),
    enabled: !!campusId,
    refetchInterval: 15_000,
    staleTime: 10_000,
  });
}
```

- [ ] **Step 2: Create `components/admin/OccupancyCard.tsx`**

```typescript
interface LotCardProps {
  nombre: string;
  nivel: string;
  total: number;
  libres: number;
  ocupados: number;
  reservados: number;
}

export default function OccupancyCard({ nombre, nivel, total, libres, ocupados, reservados }: LotCardProps) {
  const pct = total > 0 ? Math.round((ocupados / total) * 100) : 0;
  const barColor = pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-green-500';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
      <div>
        <p className="font-bold text-slate-800 text-lg">{nombre}</p>
        <p className="text-sm text-slate-500">Nivel {nivel}</p>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-600">{ocupados} / {total} ocupados</span>
          <span className="font-semibold text-slate-800">{pct}%</span>
        </div>
        <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="bg-green-50 rounded-lg p-2">
          <p className="font-bold text-green-700 text-lg">{libres}</p>
          <p className="text-green-600">Libres</p>
        </div>
        <div className="bg-red-50 rounded-lg p-2">
          <p className="font-bold text-red-700 text-lg">{ocupados}</p>
          <p className="text-red-600">Ocupados</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-2">
          <p className="font-bold text-blue-700 text-lg">{reservados}</p>
          <p className="text-blue-600">Reservados</p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update `app/(admin)/dashboard/page.tsx`**

```typescript
'use client';

import { useOccupancy } from '@/hooks/useOccupancy';
import OccupancyCard from '@/components/admin/OccupancyCard';

export default function DashboardPage() {
  const { data, isLoading, dataUpdatedAt } = useOccupancy();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
        <div className="grid grid-cols-2 gap-4">
          {[0, 1].map((i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const updatedAgo = dataUpdatedAt
    ? Math.round((Date.now() - dataUpdatedAt) / 1000)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Ocupación en tiempo real</h1>
        {updatedAgo !== null && (
          <p className="text-xs text-slate-400">
            Actualizado hace {updatedAgo}s · se actualiza cada 15s
          </p>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data?.lots.map((lot) => (
          <OccupancyCard
            key={lot.id}
            nombre={lot.nombre}
            nivel={lot.nivel}
            total={lot.total}
            libres={lot.libres}
            ocupados={lot.ocupados}
            reservados={lot.reservados}
          />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/hooks/useOccupancy.ts frontend/components/admin/OccupancyCard.tsx frontend/app/\(admin\)/dashboard/page.tsx
git commit -m "feat: add real-time occupancy dashboard with 15s polling"
```

---

### Task 3: Violations — list and table

**Files:**
- Create: `frontend/hooks/useViolations.ts`
- Create: `frontend/components/admin/ViolationTable.tsx`
- Modify: `frontend/app/(admin)/violations/page.tsx`

- [ ] **Step 1: Install shadcn table and badge**

```bash
npx shadcn-ui@latest add table
```

- [ ] **Step 2: Create `hooks/useViolations.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface ViolationType {
  id: number;
  nombre: string;
  nivel: 'leve' | 'grave' | 'muy_grave';
  descripcion: string;
}

export interface Violation {
  id: number;
  user: { id: number; nombre: string; apellido: string; codigo_institucional: string };
  vehicle: { placa: string } | null;
  tipo_falta: ViolationType;
  estado: 'PENDIENTE' | 'CONFIRMADA' | 'ANULADA';
  fecha: string;
  descripcion: string;
  sancion_propuesta?: { tipo: string; duracion_meses: number | null };
  sancion?: { tipo: string; inicio: string; fin: string | null };
}

export function useViolations(filters?: { estado?: string }) {
  const params = new URLSearchParams();
  if (filters?.estado) params.set('estado', filters.estado);
  return useQuery({
    queryKey: ['violations', filters],
    queryFn: () =>
      api.get<Violation[]>(`/violations/?${params}`).then((r) => r.data),
  });
}

export function useViolationTypes() {
  return useQuery({
    queryKey: ['violation-types'],
    queryFn: () => api.get<ViolationType[]>('/violations/types/').then((r) => r.data),
    staleTime: Infinity,
  });
}

export function useCreateViolation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { user_id: number; tipo_falta_id: number; descripcion?: string }) =>
      api.post<Violation>('/violations/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['violations'] }),
  });
}

export function useConfirmViolation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api.post<Violation>(`/violations/${id}/confirm/`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['violations'] }),
  });
}

export function useAnnulViolation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) =>
      api.post<Violation>(`/violations/${id}/annul/`, { motivo }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['violations'] }),
  });
}
```

- [ ] **Step 3: Create `components/admin/ViolationTable.tsx`**

```typescript
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useViolations } from '@/hooks/useViolations';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

const NIVEL_VARIANT: Record<string, 'default' | 'secondary' | 'destructive'> = {
  leve: 'secondary',
  grave: 'default',
  muy_grave: 'destructive',
};

const ESTADO_VARIANT: Record<string, 'default' | 'secondary' | 'outline'> = {
  PENDIENTE: 'outline',
  CONFIRMADA: 'destructive',
  ANULADA: 'secondary',
};

export default function ViolationTable() {
  const [estado, setEstado] = useState<string>('');
  const { data, isLoading } = useViolations(estado ? { estado } : undefined);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {['', 'PENDIENTE', 'CONFIRMADA', 'ANULADA'].map((s) => (
          <button
            key={s}
            onClick={() => setEstado(s)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              estado === s ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-600'
            }`}
          >
            {s || 'Todas'}
          </button>
        ))}
      </div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Usuario</TableHead>
              <TableHead>Placa</TableHead>
              <TableHead>Tipo de falta</TableHead>
              <TableHead>Nivel</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-slate-400 py-8">
                  Cargando...
                </TableCell>
              </TableRow>
            )}
            {!isLoading && !data?.length && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-slate-400 py-8">
                  No hay infracciones con el filtro seleccionado.
                </TableCell>
              </TableRow>
            )}
            {data?.map((v) => (
              <TableRow key={v.id}>
                <TableCell>
                  <p className="font-medium text-slate-800">
                    {v.user.nombre} {v.user.apellido}
                  </p>
                  <p className="text-xs text-slate-400">{v.user.codigo_institucional}</p>
                </TableCell>
                <TableCell>{v.vehicle?.placa ?? '—'}</TableCell>
                <TableCell className="max-w-xs truncate">{v.tipo_falta.nombre}</TableCell>
                <TableCell>
                  <Badge variant={NIVEL_VARIANT[v.tipo_falta.nivel]}>
                    {v.tipo_falta.nivel.replace('_', ' ')}
                  </Badge>
                </TableCell>
                <TableCell>
                  {new Date(v.fecha).toLocaleDateString('es-PE')}
                </TableCell>
                <TableCell>
                  <Badge variant={ESTADO_VARIANT[v.estado]}>{v.estado}</Badge>
                </TableCell>
                <TableCell>
                  <Link
                    href={`/violations/${v.id}`}
                    className="text-sm text-blue-700 hover:underline"
                  >
                    Ver
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update `app/(admin)/violations/page.tsx`**

```typescript
'use client';

import { useState } from 'react';
import ViolationTable from '@/components/admin/ViolationTable';
import ViolationCreateForm from '@/components/admin/ViolationCreateForm';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';

const CREATE_ROLES = ['AGENTE', 'JEFE_OPERACIONES', 'JEFE_SEGURIDAD'];

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
```

- [ ] **Step 5: Install shadcn dialog**

```bash
npx shadcn-ui@latest add dialog
```

- [ ] **Step 6: Commit**

```bash
git add frontend/hooks/useViolations.ts frontend/components/admin/ViolationTable.tsx frontend/app/\(admin\)/violations/page.tsx
git commit -m "feat: add violations list with filterable table and create dialog"
```

---

### Task 4: ViolationCreateForm with sanction proposal

**Files:**
- Create: `frontend/components/admin/ViolationCreateForm.tsx`
- Test: `frontend/components/admin/ViolationCreateForm.test.tsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/components/admin/ViolationCreateForm.test.tsx`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ViolationCreateForm from './ViolationCreateForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockCreate = vi.fn();
vi.mock('@/hooks/useViolations', () => ({
  useViolationTypes: () => ({
    data: [
      { id: 1, nombre: 'Estacionar en zona prohibida', nivel: 'leve' },
      { id: 2, nombre: 'Conducción temeraria', nivel: 'grave' },
    ],
  }),
  useCreateViolation: () => ({ mutateAsync: mockCreate, isPending: false }),
}));

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: [{ codigo_institucional: 'ALU001', nombre: 'Ana', apellido: 'García', id: 5 }],
    }),
  },
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>;
}

describe('ViolationCreateForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders user search and violation type fields', () => {
    render(<ViolationCreateForm onSuccess={() => {}} />, { wrapper });
    expect(screen.getByPlaceholderText(/código institucional/i)).toBeInTheDocument();
  });

  it('requires a violation type before submit', async () => {
    render(<ViolationCreateForm onSuccess={() => {}} />, { wrapper });
    fireEvent.click(screen.getByRole('button', { name: /registrar/i }));
    expect(await screen.findByText(/selecciona un tipo de falta/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- ViolationCreateForm.test.tsx
```
Expected: FAIL with "Cannot find module './ViolationCreateForm'"

- [ ] **Step 3: Create `components/admin/ViolationCreateForm.tsx`**

```typescript
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- ViolationCreateForm.test.tsx
```
Expected: PASS — 2 tests passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/admin/ViolationCreateForm.tsx frontend/components/admin/ViolationCreateForm.test.tsx
git commit -m "feat: add violation create form with user search and sanction preview"
```

---

### Task 5: Violation detail — confirm and annul

**Files:**
- Create: `frontend/app/(admin)/violations/[id]/page.tsx`

- [ ] **Step 1: Create `app/(admin)/violations/[id]/page.tsx`**

```typescript
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

const CONFIRM_ROLES = ['JEFE_OPERACIONES', 'JEFE_SEGURIDAD', 'DIRECTOR', 'RECTOR'];

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
        <Badge variant={v.estado === 'CONFIRMADA' ? 'destructive' : v.estado === 'ANULADA' ? 'secondary' : 'outline'}>
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
            <p className="font-medium">{v.tipo_falta.nombre}</p>
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

      {canManage && v.estado === 'PENDIENTE' && (
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/\(admin\)/violations/
git commit -m "feat: add violation detail page with confirm and annul actions"
```

---

## Plan 03 complete

Run full test suite:
```bash
npm run test
```
Expected: All tests pass (Plans 01 + 02 + ViolationCreateForm).

Admin sidebar, occupancy dashboard, and the full violations flow (list, filter, create, detail, confirm, annul) are complete. Plan 04 implements reservations, reports, spaces, and users.
