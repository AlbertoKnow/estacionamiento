# Frontend Plan 02: Field Screens — Scan, Mi QR, Vehículo, Infracciones

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all mobile-first field screens: QR scanner for agents, personal QR display for students/staff, vehicle registration, and personal violations list. Also implement the BottomNav component.

**Architecture:** All screens live under `app/(field)/` route group. They use `lib/api.ts` for data fetching via TanStack Query hooks. The QR scanner uses `html5-qrcode` library for camera access. QR display uses `qrcode.react`. Offline scan queuing is handled by Plan 05 — this plan registers the scan attempt online only.

**Prerequisites:** Plan 01 complete (auth, API client, route group layout skeleton).

**Tech Stack:** Next.js 14, TanStack Query v5, html5-qrcode, qrcode.react, Tailwind CSS, shadcn/ui, Vitest, React Testing Library

## Global Constraints
- All commands run from `frontend/` directory.
- All API calls use `api` from `@/lib/api` — never raw fetch in components.
- TypeScript strict — no `any`.
- Never add `Co-Authored-By: Claude` to git commits.
- Mobile-first: all field screens designed for 375px viewport minimum.
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/app/(field)/layout.tsx` | Modify | Replace skeleton with real BottomNav |
| `frontend/components/field/BottomNav.tsx` | Create | Bottom navigation by role |
| `frontend/hooks/useCurrentUser.ts` | Create | Get authenticated user from AuthContext |
| `frontend/app/(field)/scan/page.tsx` | Create | QR scanner page (Agent only) |
| `frontend/components/field/QrScanner.tsx` | Create | Camera + html5-qrcode wrapper |
| `frontend/components/field/ScanResult.tsx` | Create | Result card (green/red/yellow) |
| `frontend/components/field/ScanHistory.tsx` | Create | Last 10 scans of current shift |
| `frontend/hooks/useScan.ts` | Create | POST to access entry/exit endpoint |
| `frontend/app/(field)/my-qr/page.tsx` | Modify | Replace placeholder with real QR |
| `frontend/components/field/QrDisplay.tsx` | Create | Large QR + user info |
| `frontend/hooks/useMyQrToken.ts` | Create | Fetch QR token from backend |
| `frontend/app/(field)/my-vehicle/page.tsx` | Modify | Replace placeholder with form |
| `frontend/components/field/VehicleForm.tsx` | Create | Register/edit vehicle |
| `frontend/components/field/VehicleForm.test.tsx` | Create | RTL tests |
| `frontend/hooks/useMyVehicle.ts` | Create | Fetch + mutate vehicle |
| `frontend/app/(field)/my-violations/page.tsx` | Modify | Replace placeholder with list |
| `frontend/components/field/ViolationList.tsx` | Create | Personal violations list |
| `frontend/hooks/useMyViolations.ts` | Create | Fetch personal violations |

---

### Task 1: BottomNav and real field layout

**Files:**
- Create: `frontend/components/field/BottomNav.tsx`
- Modify: `frontend/app/(field)/layout.tsx`

- [ ] **Step 1: Create `components/field/BottomNav.tsx`**

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { QrCode, ScanLine, Car, AlertCircle } from 'lucide-react';

const AGENT_ITEMS = [
  { href: '/scan', label: 'Escanear', icon: ScanLine },
];

const USER_ITEMS = [
  { href: '/my-qr', label: 'Mi QR', icon: QrCode },
  { href: '/my-vehicle', label: 'Vehículo', icon: Car },
  { href: '/my-violations', label: 'Infracciones', icon: AlertCircle },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user?.rol === 'AGENTE' ? AGENT_ITEMS : USER_ITEMS;

  return (
    <nav className="h-16 bg-white border-t border-slate-200 flex items-center">
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`flex-1 flex flex-col items-center justify-center gap-0.5 text-xs ${
              active ? 'text-blue-700 font-semibold' : 'text-slate-500'
            }`}
          >
            <Icon size={20} strokeWidth={active ? 2.5 : 1.5} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 2: Install lucide-react**

```bash
npm install lucide-react
```

- [ ] **Step 3: Update `app/(field)/layout.tsx`**

```typescript
import BottomNav from '@/components/field/BottomNav';

export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-50 max-w-md mx-auto">
      <main className="flex-1 overflow-auto">{children}</main>
      <BottomNav />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/field/BottomNav.tsx frontend/app/\(field\)/layout.tsx
git commit -m "feat: add field layout with role-aware bottom navigation"
```

---

### Task 2: /scan — QR Scanner for Agents

**Files:**
- Create: `frontend/hooks/useScan.ts`
- Create: `frontend/components/field/ScanResult.tsx`
- Create: `frontend/components/field/ScanHistory.tsx`
- Create: `frontend/components/field/QrScanner.tsx`
- Modify: `frontend/app/(field)/scan/page.tsx`

**Interfaces:**
- Produces: `useScan()` hook with `{ scan(qr_token: string, tipo: 'entry'|'exit'): Promise<ScanResponse>, lastResult, history }`

- [ ] **Step 1: Create `hooks/useScan.ts`**

```typescript
import { useState, useCallback } from 'react';
import api from '@/lib/api';

export type ScanStatus = 'idle' | 'success' | 'error' | 'offline';

export interface ScanResultData {
  status: ScanStatus;
  nombre?: string;
  placa?: string;
  tipo?: 'entry' | 'exit';
  message?: string;
  timestamp: Date;
}

export function useScan() {
  const [lastResult, setLastResult] = useState<ScanResultData | null>(null);
  const [history, setHistory] = useState<ScanResultData[]>([]);

  const scan = useCallback(async (qr_token: string, tipo: 'entry' | 'exit') => {
    const timestamp = new Date();
    if (!navigator.onLine) {
      const result: ScanResultData = { status: 'offline', tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
    try {
      const endpoint = tipo === 'entry' ? '/access/entry/' : '/access/exit/';
      const res = await api.post<{ usuario: string; placa: string }>(endpoint, { qr_token });
      const result: ScanResultData = {
        status: 'success',
        nombre: res.data.usuario,
        placa: res.data.placa,
        tipo,
        timestamp,
      };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'QR inválido o expirado.';
      const result: ScanResultData = { status: 'error', message: msg, tipo, timestamp };
      setLastResult(result);
      setHistory((prev) => [result, ...prev].slice(0, 10));
      return result;
    }
  }, []);

  return { scan, lastResult, history };
}
```

- [ ] **Step 2: Create `components/field/ScanResult.tsx`**

```typescript
import { useEffect, useState } from 'react';
import { ScanResultData } from '@/hooks/useScan';
import { CheckCircle, XCircle, WifiOff } from 'lucide-react';

interface Props {
  result: ScanResultData;
  onDismiss: () => void;
}

const CONFIG = {
  success: {
    bg: 'bg-green-50 border-green-200',
    text: 'text-green-800',
    icon: CheckCircle,
    iconColor: 'text-green-600',
  },
  error: {
    bg: 'bg-red-50 border-red-200',
    text: 'text-red-800',
    icon: XCircle,
    iconColor: 'text-red-600',
  },
  offline: {
    bg: 'bg-amber-50 border-amber-200',
    text: 'text-amber-800',
    icon: WifiOff,
    iconColor: 'text-amber-600',
  },
  idle: {
    bg: 'bg-slate-50 border-slate-200',
    text: 'text-slate-800',
    icon: CheckCircle,
    iconColor: 'text-slate-400',
  },
};

export default function ScanResult({ result, onDismiss }: Props) {
  const [visible, setVisible] = useState(true);
  const cfg = CONFIG[result.status];
  const Icon = cfg.icon;

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300);
    }, 4000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const label =
    result.status === 'success'
      ? `${result.tipo === 'entry' ? 'ENTRADA' : 'SALIDA'} REGISTRADA`
      : result.status === 'offline'
      ? 'REGISTRADO LOCALMENTE'
      : 'ACCESO DENEGADO';

  return (
    <div
      className={`transition-opacity duration-300 ${visible ? 'opacity-100' : 'opacity-0'} border rounded-xl p-4 ${cfg.bg}`}
    >
      <div className="flex items-center gap-3">
        <Icon size={32} className={cfg.iconColor} />
        <div>
          <p className={`font-bold text-lg ${cfg.text}`}>{label}</p>
          {result.nombre && (
            <p className={`text-sm ${cfg.text}`}>
              {result.nombre} · {result.placa}
            </p>
          )}
          {result.message && <p className={`text-sm ${cfg.text}`}>{result.message}</p>}
          {result.status === 'offline' && (
            <p className={`text-xs ${cfg.text} mt-1`}>
              Se sincronizará al recuperar señal
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `components/field/ScanHistory.tsx`**

```typescript
import { ScanResultData } from '@/hooks/useScan';
import { CheckCircle, XCircle, WifiOff } from 'lucide-react';

const STATUS_ICON = {
  success: { Icon: CheckCircle, color: 'text-green-500' },
  error: { Icon: XCircle, color: 'text-red-500' },
  offline: { Icon: WifiOff, color: 'text-amber-500' },
  idle: { Icon: CheckCircle, color: 'text-slate-300' },
};

export default function ScanHistory({ items }: { items: ScanResultData[] }) {
  if (!items.length) return null;
  return (
    <div className="mt-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">Últimos escaneos</p>
      <ul className="space-y-1">
        {items.map((item, i) => {
          const { Icon, color } = STATUS_ICON[item.status];
          return (
            <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
              <Icon size={14} className={color} />
              <span className="flex-1 truncate">{item.nombre ?? item.message ?? 'Sin señal'}</span>
              <span className="text-xs text-slate-400">
                {item.timestamp.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
```

- [ ] **Step 4: Create `components/field/QrScanner.tsx`**

```typescript
'use client';

import { useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';

interface Props {
  onScan: (token: string) => void;
  paused?: boolean;
}

export default function QrScanner({ onScan, paused }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const scanner = new Html5QrcodeScanner(
      'qr-reader',
      { fps: 10, qrbox: { width: 250, height: 250 }, aspectRatio: 1 },
      false
    );
    scannerRef.current = scanner;
    scanner.render(
      (text) => {
        if (!paused) onScan(text);
      },
      () => {}
    );
    return () => {
      scanner.clear().catch(() => {});
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full">
      <div ref={containerRef} id="qr-reader" className="w-full" />
    </div>
  );
}
```

- [ ] **Step 5: Update `app/(field)/scan/page.tsx`**

```typescript
'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useScan } from '@/hooks/useScan';
import ScanResult from '@/components/field/ScanResult';
import ScanHistory from '@/components/field/ScanHistory';

// html5-qrcode requires browser APIs — dynamic import with no SSR
const QrScanner = dynamic(() => import('@/components/field/QrScanner'), { ssr: false });

export default function ScanPage() {
  const { scan, lastResult, history } = useScan();
  const [paused, setPaused] = useState(false);
  const [tipo, setTipo] = useState<'entry' | 'exit'>('entry');

  const handleScan = useCallback(
    async (token: string) => {
      setPaused(true);
      await scan(token, tipo);
    },
    [scan, tipo]
  );

  const handleDismiss = useCallback(() => {
    setPaused(false);
  }, []);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-800">Escanear QR</h1>
        <div className="flex gap-2">
          {(['entry', 'exit'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTipo(t)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                tipo === t
                  ? 'bg-blue-700 text-white'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {t === 'entry' ? 'Entrada' : 'Salida'}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl overflow-hidden border border-slate-200 bg-black">
        <QrScanner onScan={handleScan} paused={paused} />
      </div>

      {lastResult && <ScanResult result={lastResult} onDismiss={handleDismiss} />}
      <ScanHistory items={history} />
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/hooks/useScan.ts frontend/components/field/ frontend/app/\(field\)/scan/page.tsx
git commit -m "feat: add QR scanner screen with result cards and shift history"
```

---

### Task 3: /my-qr — Personal QR Display

**Files:**
- Create: `frontend/hooks/useMyQrToken.ts`
- Create: `frontend/components/field/QrDisplay.tsx`
- Modify: `frontend/app/(field)/my-qr/page.tsx`

- [ ] **Step 1: Create `hooks/useMyQrToken.ts`**

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface QrTokenResponse {
  qr_token: string;
  expires_at: string;
}

export function useMyQrToken() {
  return useQuery({
    queryKey: ['my-qr-token'],
    queryFn: () => api.get<QrTokenResponse>('/auth/qr-token/').then((r) => r.data),
    staleTime: 1000 * 60 * 4, // refresh before 5-min JWT expiry
    refetchInterval: 1000 * 60 * 4,
  });
}
```

- [ ] **Step 2: Install qrcode.react**

```bash
npm install qrcode.react
```

- [ ] **Step 3: Create `components/field/QrDisplay.tsx`**

```typescript
'use client';

import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '@/contexts/AuthContext';
import { useMyQrToken } from '@/hooks/useMyQrToken';
import { RefreshCw } from 'lucide-react';

export default function QrDisplay() {
  const { user } = useAuth();
  const { data, isLoading, refetch, isRefetching } = useMyQrToken();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center p-8 text-slate-500">
        No se pudo obtener el código QR.
        <button onClick={() => refetch()} className="block mx-auto mt-2 text-blue-700 underline">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <div className="bg-white p-4 rounded-2xl shadow-md border border-slate-100">
        <QRCodeSVG value={data.qr_token} size={240} level="M" />
      </div>
      <div className="text-center">
        <p className="text-xl font-bold text-slate-800">
          {user?.nombre} {user?.apellido}
        </p>
        <p className="text-sm text-slate-500">{user?.codigo_institucional}</p>
      </div>
      <button
        onClick={() => refetch()}
        disabled={isRefetching}
        className="flex items-center gap-1 text-sm text-blue-700 disabled:opacity-50"
      >
        <RefreshCw size={14} className={isRefetching ? 'animate-spin' : ''} />
        Actualizar QR
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Update `app/(field)/my-qr/page.tsx`**

```typescript
import QrDisplay from '@/components/field/QrDisplay';
import Link from 'next/link';

export default function MyQrPage() {
  return (
    <div className="p-4">
      <h1 className="text-lg font-bold text-slate-800 mb-4 text-center">Mi Código QR</h1>
      <QrDisplay />
      <p className="text-center text-xs text-slate-400 mt-4">
        Muestra este código al agente de seguridad en el ingreso
      </p>
      <div className="mt-4 text-center">
        <Link href="/my-vehicle" className="text-sm text-blue-700 underline">
          Gestionar vehículo
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/hooks/useMyQrToken.ts frontend/components/field/QrDisplay.tsx frontend/app/\(field\)/my-qr/page.tsx
git commit -m "feat: add personal QR display screen with auto-refresh"
```

---

### Task 4: /my-vehicle — Vehicle Registration

**Files:**
- Create: `frontend/hooks/useMyVehicle.ts`
- Create: `frontend/components/field/VehicleForm.tsx`
- Test: `frontend/components/field/VehicleForm.test.tsx`
- Modify: `frontend/app/(field)/my-vehicle/page.tsx`

- [ ] **Step 1: Install shadcn select component**

```bash
npx shadcn-ui@latest add select
```

- [ ] **Step 2: Write failing tests**

Create `frontend/components/field/VehicleForm.test.tsx`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import VehicleForm from './VehicleForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockMutate = vi.fn();
vi.mock('@/hooks/useMyVehicle', () => ({
  useMyVehicle: () => ({ data: null, isLoading: false }),
  useUpsertVehicle: () => ({ mutateAsync: mockMutate, isPending: false }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      {children}
    </QueryClientProvider>
  );
}

describe('VehicleForm', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders placa and tipo fields', () => {
    render(<VehicleForm />, { wrapper });
    expect(screen.getByLabelText(/placa/i)).toBeInTheDocument();
  });

  it('validates placa format', async () => {
    render(<VehicleForm />, { wrapper });
    await userEvent.type(screen.getByLabelText(/placa/i), 'INVALID');
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }));
    expect(await screen.findByText(/formato de placa inválido/i)).toBeInTheDocument();
  });

  it('submits valid placa', async () => {
    mockMutate.mockResolvedValue({});
    render(<VehicleForm />, { wrapper });
    await userEvent.type(screen.getByLabelText(/placa/i), 'ABC-123');
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }));
    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(expect.objectContaining({ placa: 'ABC-123' }))
    );
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
npm run test -- VehicleForm.test.tsx
```
Expected: FAIL with "Cannot find module './VehicleForm'"

- [ ] **Step 4: Create `hooks/useMyVehicle.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

interface Vehicle {
  id: number;
  placa: string;
  tipo: string;
  marca: string;
  modelo: string;
  color: string;
}

export function useMyVehicle() {
  return useQuery({
    queryKey: ['my-vehicle'],
    queryFn: () =>
      api.get<Vehicle[]>('/vehicles/my/').then((r) => r.data[0] ?? null),
  });
}

export function useUpsertVehicle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Vehicle>) =>
      data.id
        ? api.patch(`/vehicles/${data.id}/`, data).then((r) => r.data)
        : api.post('/vehicles/', data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-vehicle'] }),
  });
}
```

- [ ] **Step 5: Create `components/field/VehicleForm.tsx`**

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useMyVehicle, useUpsertVehicle } from '@/hooks/useMyVehicle';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const PLACA_REGEX = /^[A-Z0-9]{3}-?[A-Z0-9]{3}$/i;
const TIPOS = ['AUTO', 'CAMIONETA', 'MOTO', 'OTRO'];

export default function VehicleForm() {
  const { data: vehicle } = useMyVehicle();
  const { mutateAsync, isPending } = useUpsertVehicle();

  const [placa, setPlaca] = useState('');
  const [tipo, setTipo] = useState('AUTO');
  const [marca, setMarca] = useState('');
  const [modelo, setModelo] = useState('');
  const [color, setColor] = useState('');
  const [placaError, setPlacaError] = useState('');

  useEffect(() => {
    if (vehicle) {
      setPlaca(vehicle.placa);
      setTipo(vehicle.tipo);
      setMarca(vehicle.marca ?? '');
      setModelo(vehicle.modelo ?? '');
      setColor(vehicle.color ?? '');
    }
  }, [vehicle]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPlacaError('');
    if (!PLACA_REGEX.test(placa)) {
      setPlacaError('Formato de placa inválido (ej: ABC-123)');
      return;
    }
    try {
      await mutateAsync({ id: vehicle?.id, placa: placa.toUpperCase(), tipo, marca, modelo, color });
      toast.success('Vehículo guardado correctamente');
    } catch {
      toast.error('Error al guardar el vehículo');
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4">
      <div>
        <Label htmlFor="placa">Placa</Label>
        <Input
          id="placa"
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          placeholder="ABC-123"
          className="uppercase"
        />
        {placaError && <p className="text-sm text-destructive mt-1">{placaError}</p>}
      </div>
      <div>
        <Label htmlFor="tipo">Tipo de vehículo</Label>
        <select
          id="tipo"
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="w-full h-10 px-3 border border-input rounded-md text-sm bg-background"
        >
          {TIPOS.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>
      <div>
        <Label htmlFor="marca">Marca</Label>
        <Input id="marca" value={marca} onChange={(e) => setMarca(e.target.value)} placeholder="Toyota" />
      </div>
      <div>
        <Label htmlFor="modelo">Modelo (opcional)</Label>
        <Input id="modelo" value={modelo} onChange={(e) => setModelo(e.target.value)} placeholder="Corolla" />
      </div>
      <div>
        <Label htmlFor="color">Color (opcional)</Label>
        <Input id="color" value={color} onChange={(e) => setColor(e.target.value)} placeholder="Blanco" />
      </div>
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? 'Guardando...' : 'Guardar vehículo'}
      </Button>
    </form>
  );
}
```

- [ ] **Step 6: Update `app/(field)/my-vehicle/page.tsx`**

```typescript
import VehicleForm from '@/components/field/VehicleForm';

export default function MyVehiclePage() {
  return (
    <div>
      <div className="p-4 border-b border-slate-200 bg-white">
        <h1 className="text-lg font-bold text-slate-800">Mi Vehículo</h1>
      </div>
      <VehicleForm />
    </div>
  );
}
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
npm run test -- VehicleForm.test.tsx
```
Expected: PASS — 3 tests passed.

- [ ] **Step 8: Commit**

```bash
git add frontend/hooks/useMyVehicle.ts frontend/components/field/VehicleForm.tsx frontend/components/field/VehicleForm.test.tsx frontend/app/\(field\)/my-vehicle/page.tsx
git commit -m "feat: add vehicle registration form with placa validation"
```

---

### Task 5: /my-violations — Personal Violations List

**Files:**
- Create: `frontend/hooks/useMyViolations.ts`
- Create: `frontend/components/field/ViolationList.tsx`
- Modify: `frontend/app/(field)/my-violations/page.tsx`

- [ ] **Step 1: Create `hooks/useMyViolations.ts`**

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface ViolationItem {
  id: number;
  tipo_falta: { nombre: string; nivel: 'leve' | 'grave' | 'muy_grave' };
  fecha: string;
  estado: 'PENDIENTE' | 'CONFIRMADA' | 'ANULADA';
  descripcion: string;
  sancion?: { tipo: string; inicio: string; fin: string | null };
}

export function useMyViolations() {
  return useQuery({
    queryKey: ['my-violations'],
    queryFn: () => api.get<ViolationItem[]>('/violations/my/').then((r) => r.data),
  });
}
```

- [ ] **Step 2: Create `components/field/ViolationList.tsx`**

```typescript
'use client';

import { useMyViolations } from '@/hooks/useMyViolations';

const NIVEL_CONFIG = {
  leve: { label: 'Leve', bg: 'bg-yellow-100 text-yellow-800' },
  grave: { label: 'Grave', bg: 'bg-orange-100 text-orange-800' },
  muy_grave: { label: 'Muy Grave', bg: 'bg-red-100 text-red-800' },
};

const ESTADO_CONFIG = {
  PENDIENTE: 'bg-slate-100 text-slate-600',
  CONFIRMADA: 'bg-red-100 text-red-700',
  ANULADA: 'bg-green-100 text-green-700',
};

export default function ViolationList() {
  const { data, isLoading } = useMyViolations();

  if (isLoading) {
    return <div className="p-4 text-slate-500">Cargando...</div>;
  }

  if (!data?.length) {
    return (
      <div className="p-8 text-center text-slate-400">
        No tienes infracciones registradas.
      </div>
    );
  }

  return (
    <ul className="divide-y divide-slate-100">
      {data.map((v) => {
        const nivel = NIVEL_CONFIG[v.tipo_falta.nivel];
        const estadoCls = ESTADO_CONFIG[v.estado];
        return (
          <li key={v.id} className="p-4 space-y-1 bg-white">
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${nivel.bg}`}>
                {nivel.label}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${estadoCls}`}>
                {v.estado}
              </span>
            </div>
            <p className="text-sm font-medium text-slate-800">{v.tipo_falta.nombre}</p>
            <p className="text-xs text-slate-500">
              {new Date(v.fecha).toLocaleDateString('es-PE')}
            </p>
            {v.sancion && v.estado === 'CONFIRMADA' && (
              <p className="text-xs text-red-600">
                Sanción: {v.sancion.tipo}
                {v.sancion.fin ? ` hasta ${new Date(v.sancion.fin).toLocaleDateString('es-PE')}` : ''}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
```

- [ ] **Step 3: Update `app/(field)/my-violations/page.tsx`**

```typescript
import ViolationList from '@/components/field/ViolationList';

export default function MyViolationsPage() {
  return (
    <div>
      <div className="p-4 border-b border-slate-200 bg-white">
        <h1 className="text-lg font-bold text-slate-800">Mis Infracciones</h1>
      </div>
      <ViolationList />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/hooks/useMyViolations.ts frontend/components/field/ViolationList.tsx frontend/app/\(field\)/my-violations/page.tsx
git commit -m "feat: add personal violations list screen"
```

---

## Plan 02 complete

Run full test suite:
```bash
npm run test
```
Expected: All tests pass (Plan 01 + VehicleForm).

All field screens are complete: `/scan` with QR camera, `/my-qr` with QR display, `/my-vehicle` with placa validation, and `/my-violations` with violation list. Plan 03 implements the admin screens.
