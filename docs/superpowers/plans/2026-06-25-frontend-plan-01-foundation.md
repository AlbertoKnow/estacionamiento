# Frontend Plan 01: Foundation — Setup, Auth y Routing

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Next.js 14 frontend, install all dependencies, implement JWT auth with httpOnly cookie, Axios API client with automatic token refresh, role-based middleware, and a working login page.

**Architecture:** Next.js 14 App Router inside `frontend/` subdirectory of the existing Django monorepo. Access token lives in memory (AuthContext). Refresh token lives in a Next.js-managed httpOnly cookie. A proxy route at `/api/auth/token` handles the cookie server-side. Middleware reads a non-httpOnly `utp_role` cookie (set at login, used only for UX routing — real security is backend-enforced).

**Tech Stack:** Next.js 14, TypeScript strict, Tailwind CSS, shadcn/ui, Axios 1.x, TanStack Query v5, Vitest, React Testing Library, @testing-library/jest-dom

## Global Constraints
- Node.js >= 20 required. Run all commands from `frontend/` directory.
- TypeScript `strict: true` — no `any` unless explicitly justified.
- All API calls go through `lib/api.ts` — never use `fetch` directly in components.
- Backend runs at `http://localhost:8000` (docker compose up from project root).
- Never store access token in `localStorage` or `sessionStorage` — memory only.
- Never add `Co-Authored-By: Claude` to git commits.
- shadcn/ui components installed individually as needed — no bulk install.
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `frontend/` | Create | Next.js project root |
| `frontend/.env.local` | Create | Env vars (gitignored) |
| `frontend/vitest.config.ts` | Create | Vitest + jsdom config |
| `frontend/tests/setup.ts` | Create | jest-dom matchers |
| `frontend/lib/api.types.ts` | Generate | OpenAPI types from backend |
| `frontend/lib/auth.ts` | Create | Access token in memory + cookie helpers |
| `frontend/lib/auth.test.ts` | Create | Unit tests for auth module |
| `frontend/app/api/auth/token/route.ts` | Create | httpOnly cookie proxy |
| `frontend/lib/api.ts` | Create | Axios instance + interceptors |
| `frontend/lib/api.test.ts` | Create | Interceptor unit tests |
| `frontend/contexts/AuthContext.tsx` | Create | Access token + user state |
| `frontend/app/layout.tsx` | Create | Root layout with providers |
| `frontend/middleware.ts` | Create | Route protection + role redirect |
| `frontend/app/login/page.tsx` | Create | Login page |
| `frontend/components/LoginForm.tsx` | Create | Login form with validation |
| `frontend/components/LoginForm.test.tsx` | Create | RTL tests for login form |
| `frontend/app/(admin)/layout.tsx` | Create | Sidebar shell (skeleton) |
| `frontend/app/(field)/layout.tsx` | Create | Bottom nav shell (skeleton) |

---

### Task 1: Scaffold Next.js project and install dependencies

**Files:**
- Create: `frontend/` (Next.js project)
- Create: `frontend/.env.local`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/tests/setup.ts`

- [ ] **Step 1: Create Next.js app**

From the repo root (`estacionamiento/`):
```bash
npx create-next-app@14 frontend --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"
```
When prompted, accept all defaults.

- [ ] **Step 2: Install runtime dependencies**

```bash
cd frontend
npm install axios @tanstack/react-query @tanstack/react-query-devtools dexie html5-qrcode qrcode.react
```

- [ ] **Step 3: Install dev dependencies**

```bash
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom fake-indexeddb openapi-typescript @playwright/test
```

- [ ] **Step 4: Install shadcn/ui**

```bash
npx shadcn-ui@latest init
```
When prompted: Style=Default, Base color=Slate, CSS variables=yes.

- [ ] **Step 5: Install shadcn components needed for Plan 01**

```bash
npx shadcn-ui@latest add button input label card sonner
```

- [ ] **Step 6: Create `.env.local`**

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
API_URL=http://localhost:8000/api/v1
```

- [ ] **Step 7: Create `vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, '.') },
  },
});
```

- [ ] **Step 8: Create `tests/setup.ts`**

```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 9: Add test scripts to `package.json`**

In `frontend/package.json`, add to `"scripts"`:
```json
"test": "vitest run",
"test:watch": "vitest",
"test:e2e": "playwright test",
"types:api": "openapi-typescript http://localhost:8000/api/v1/schema/ -o lib/api.types.ts"
```

- [ ] **Step 10: Verify setup**

```bash
npm run test
```
Expected: "No test files found" (0 tests, no failures).

- [ ] **Step 11: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: scaffold Next.js 14 frontend with TypeScript, Tailwind, shadcn/ui, Vitest"
```

---

### Task 2: Generate API types from OpenAPI schema

**Files:**
- Create: `frontend/lib/api.types.ts` (auto-generated)

**Prerequisite:** Docker backend must be running (`docker compose up` from repo root).

- [ ] **Step 1: Generate types**

```bash
cd frontend
npm run types:api
```
Expected: `lib/api.types.ts` created with ~500+ lines of TypeScript types.

- [ ] **Step 2: Verify the file contains key types**

Open `frontend/lib/api.types.ts` and confirm these schemas exist:
- `components['schemas']['CustomUser']`
- `components['schemas']['Violation']`
- `components['schemas']['Reservation']`

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/api.types.ts
git commit -m "feat: generate TypeScript types from Django OpenAPI schema"
```

---

### Task 3: Auth module — access token in memory

**Files:**
- Create: `frontend/lib/auth.ts`
- Test: `frontend/lib/auth.test.ts`

**Interfaces:**
- Produces: `setAccessToken(token: string): void`, `getAccessToken(): string | null`, `clearAccessToken(): void`, `storeRefreshCookie(refresh: string): Promise<void>`, `refreshAccessToken(): Promise<string>`, `clearRefreshCookie(): Promise<void>`

- [ ] **Step 1: Write failing tests**

Create `frontend/lib/auth.test.ts`:
```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setAccessToken, getAccessToken, clearAccessToken } from './auth';

describe('auth token management', () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it('returns null when no token set', () => {
    expect(getAccessToken()).toBeNull();
  });

  it('stores and retrieves access token', () => {
    setAccessToken('test-token-abc');
    expect(getAccessToken()).toBe('test-token-abc');
  });

  it('clears access token', () => {
    setAccessToken('test-token-abc');
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });

  it('overwrites existing token', () => {
    setAccessToken('token-1');
    setAccessToken('token-2');
    expect(getAccessToken()).toBe('token-2');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- auth.test.ts
```
Expected: FAIL with "Cannot find module './auth'"

- [ ] **Step 3: Implement `lib/auth.ts`**

```typescript
let _accessToken: string | null = null;

export const setAccessToken = (token: string): void => {
  _accessToken = token;
};

export const getAccessToken = (): string | null => _accessToken;

export const clearAccessToken = (): void => {
  _accessToken = null;
};

export async function storeRefreshCookie(refresh: string): Promise<void> {
  await fetch('/api/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
}

export async function refreshAccessToken(): Promise<string> {
  const res = await fetch('/api/auth/token', { method: 'GET' });
  if (!res.ok) throw new Error('refresh_failed');
  const data = await res.json();
  setAccessToken(data.access);
  return data.access;
}

export async function clearRefreshCookie(): Promise<void> {
  await fetch('/api/auth/token', { method: 'DELETE' });
  clearAccessToken();
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- auth.test.ts
```
Expected: PASS — 4 tests passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/auth.ts frontend/lib/auth.test.ts
git commit -m "feat: add auth token management (access in memory)"
```

---

### Task 4: httpOnly cookie proxy route

**Files:**
- Create: `frontend/app/api/auth/token/route.ts`

- [ ] **Step 1: Create the proxy route**

Create `frontend/app/api/auth/token/route.ts`:
```typescript
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_URL = process.env.API_URL ?? 'http://localhost:8000/api/v1';
const COOKIE_NAME = 'utp_refresh';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7; // 7 days

// GET → use stored refresh cookie to get new access token from Django
export async function GET() {
  const cookieStore = cookies();
  const refresh = cookieStore.get(COOKIE_NAME)?.value;
  if (!refresh) {
    return NextResponse.json({ detail: 'No refresh token' }, { status: 401 });
  }
  const res = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    const response = NextResponse.json({ detail: 'Token refresh failed' }, { status: 401 });
    response.cookies.delete(COOKIE_NAME);
    return response;
  }
  const data = await res.json();
  return NextResponse.json({ access: data.access });
}

// POST → store refresh token in httpOnly cookie
export async function POST(request: Request) {
  const { refresh } = await request.json();
  const response = NextResponse.json({ ok: true });
  response.cookies.set(COOKIE_NAME, refresh, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: COOKIE_MAX_AGE,
    path: '/',
  });
  return response;
}

// DELETE → clear the cookie (logout)
export async function DELETE() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(COOKIE_NAME);
  return response;
}
```

- [ ] **Step 2: Verify build compiles**

```bash
npm run build 2>&1 | head -20
```
Expected: no TypeScript errors in the route file.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/api/auth/token/route.ts
git commit -m "feat: add httpOnly cookie proxy route for JWT refresh token"
```

---

### Task 5: Axios API client with automatic token refresh

**Files:**
- Create: `frontend/lib/api.ts`
- Test: `frontend/lib/api.test.ts`

**Interfaces:**
- Consumes: `getAccessToken()`, `setAccessToken()`, `clearAccessToken()` from `lib/auth`
- Produces: `api` (default export — Axios instance), used by all hooks and components

- [ ] **Step 1: Write failing test**

Create `frontend/lib/api.test.ts`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock auth module
vi.mock('./auth', () => ({
  getAccessToken: vi.fn(() => 'mock-access-token'),
  setAccessToken: vi.fn(),
  clearAccessToken: vi.fn(),
}));

// Mock fetch for the refresh proxy
global.fetch = vi.fn();

describe('api client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('exports a default axios instance', async () => {
    const { default: api } = await import('./api');
    expect(api).toBeDefined();
    expect(typeof api.get).toBe('function');
    expect(typeof api.post).toBe('function');
  });

  it('has baseURL configured', async () => {
    const { default: api } = await import('./api');
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api/v1');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm run test -- api.test.ts
```
Expected: FAIL with "Cannot find module './api'"

- [ ] **Step 3: Implement `lib/api.ts`**

```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { getAccessToken, setAccessToken, clearAccessToken } from './auth';

const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
type QueueEntry = { resolve: (token: string) => void; reject: (err: unknown) => void };
let failedQueue: QueueEntry[] = [];

function processQueue(error: unknown, token: string | null): void {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      });
    }
    original._retry = true;
    isRefreshing = true;
    try {
      const res = await fetch('/api/auth/token');
      if (!res.ok) throw new Error('refresh_failed');
      const data = await res.json();
      setAccessToken(data.access);
      processQueue(null, data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (err) {
      processQueue(err, null);
      clearAccessToken();
      if (typeof window !== 'undefined') window.location.href = '/login';
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test -- api.test.ts
```
Expected: PASS — 2 tests passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/api.ts frontend/lib/api.test.ts
git commit -m "feat: add Axios API client with automatic JWT refresh on 401"
```

---

### Task 6: AuthContext and providers

**Files:**
- Create: `frontend/contexts/AuthContext.tsx`
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Produces: `useAuth(): { user: AuthUser | null, login(codigo, password): Promise<void>, logout(): Promise<void>, isLoading: boolean }`
- Produces type: `AuthUser { id, codigo_institucional, nombre, apellido, rol, campus_asignado }`

- [ ] **Step 1: Create `contexts/AuthContext.tsx`**

```typescript
'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import {
  setAccessToken,
  clearAccessToken,
  storeRefreshCookie,
  refreshAccessToken,
  clearRefreshCookie,
} from '@/lib/auth';

export interface AuthUser {
  id: number;
  codigo_institucional: string;
  nombre: string;
  apellido: string;
  rol: string;
  campus_asignado: { id: number; nombre: string } | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (codigo: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, attempt silent refresh to restore session
  useEffect(() => {
    refreshAccessToken()
      .then(() => api.get<AuthUser>('/auth/me/').then((r) => setUser(r.data)))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (codigo: string, password: string) => {
    const res = await api.post<{ access: string; refresh: string; user: AuthUser }>(
      '/auth/login/',
      { codigo_institucional: codigo, password }
    );
    setAccessToken(res.data.access);
    await storeRefreshCookie(res.data.refresh);
    // Store role in a readable cookie for middleware routing
    document.cookie = `utp_role=${res.data.user.rol}; path=/; SameSite=Lax`;
    setUser(res.data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      const token = (await import('@/lib/auth')).getAccessToken();
      if (token) await api.post('/auth/logout/', { refresh: token });
    } catch {}
    await clearRefreshCookie();
    clearAccessToken();
    document.cookie = 'utp_role=; path=/; max-age=0';
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
```

- [ ] **Step 2: Update `app/layout.tsx`**

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import QueryProvider from '@/contexts/QueryProvider';
import { Toaster } from '@/components/ui/sonner';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'UTP Parking',
  description: 'Sistema de estacionamiento UTP Arequipa',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <QueryProvider>
          <AuthProvider>
            {children}
            <Toaster position="bottom-right" />
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Create `contexts/QueryProvider.tsx`**

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, staleTime: 30_000 },
        },
      })
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 4: Verify build compiles**

```bash
npm run build 2>&1 | grep -E "error|Error" | head -10
```
Expected: no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/contexts/ frontend/app/layout.tsx
git commit -m "feat: add AuthContext with login/logout and QueryClientProvider"
```

---

### Task 7: Middleware — route protection and role-based redirect

**Files:**
- Create: `frontend/middleware.ts`

- [ ] **Step 1: Create `middleware.ts`**

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const REFRESH_COOKIE = 'utp_refresh';
const ROLE_COOKIE = 'utp_role';

const FIELD_ROLES = new Set(['AGENTE', 'ALUMNO', 'DOCENTE', 'ADMINISTRATIVO', 'VISITANTE']);
const ADMIN_ONLY_PATHS = ['/dashboard', '/reservations', '/reports', '/spaces', '/users'];
const AGENT_PATH = '/scan';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Pass through public and internal routes
  if (
    pathname.startsWith('/login') ||
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/icons/')
  ) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.has(REFRESH_COOKIE);
  if (!hasSession) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  const role = request.cookies.get(ROLE_COOKIE)?.value ?? '';

  // Agente trying to access admin-only paths
  if (ADMIN_ONLY_PATHS.some((p) => pathname.startsWith(p)) && FIELD_ROLES.has(role)) {
    const dest = role === 'AGENTE' ? '/scan' : '/my-qr';
    return NextResponse.redirect(new URL(dest, request.url));
  }

  // Non-agente trying to access scan
  if (pathname.startsWith(AGENT_PATH) && role !== 'AGENTE') {
    return NextResponse.redirect(new URL('/my-qr', request.url));
  }

  // Admin roles trying to access field-only paths
  if ((pathname.startsWith('/my-qr') || pathname.startsWith('/my-vehicle') || pathname.startsWith('/my-violations')) && !FIELD_ROLES.has(role)) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/middleware.ts
git commit -m "feat: add Next.js middleware for route protection and role-based redirect"
```

---

### Task 8: Login page and LoginForm component

**Files:**
- Create: `frontend/app/login/page.tsx`
- Create: `frontend/components/LoginForm.tsx`
- Test: `frontend/components/LoginForm.test.tsx`

**Interfaces:**
- Consumes: `useAuth()` from `contexts/AuthContext`

- [ ] **Step 1: Write failing tests**

Create `frontend/components/LoginForm.test.tsx`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

const mockLogin = vi.fn();
const mockPush = vi.fn();

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin, user: null, isLoading: false }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders codigo and password fields', () => {
    render(<LoginForm />);
    expect(screen.getByLabelText(/código institucional/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
  });

  it('shows validation error when fields are empty', async () => {
    render(<LoginForm />);
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/campo requerido/i)).toBeInTheDocument();
  });

  it('calls login with form values on submit', async () => {
    mockLogin.mockResolvedValue(undefined);
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText(/código institucional/i), 'ALU001');
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'pass123');
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('ALU001', 'pass123'));
  });

  it('shows error message on login failure', async () => {
    mockLogin.mockRejectedValue({
      response: { data: { detail: 'Credenciales inválidas.' } },
    });
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText(/código institucional/i), 'ALU001');
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'wrong');
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/credenciales inválidas/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npm run test -- LoginForm.test.tsx
```
Expected: FAIL with "Cannot find module './LoginForm'"

- [ ] **Step 3: Create `components/LoginForm.tsx`**

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ROLE_REDIRECTS: Record<string, string> = {
  AGENTE: '/scan',
  ALUMNO: '/my-qr',
  DOCENTE: '/my-qr',
  ADMINISTRATIVO: '/my-qr',
  VISITANTE: '/my-qr',
  JEFE_OPERACIONES: '/dashboard',
  JEFE_SEGURIDAD: '/dashboard',
  DIRECTOR: '/dashboard',
  RECTOR: '/dashboard',
};

export default function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [codigo, setCodigo] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setFieldError('');
    if (!codigo.trim() || !password.trim()) {
      setFieldError('Campo requerido');
      return;
    }
    setIsLoading(true);
    try {
      await login(codigo.trim(), password);
      // Role comes from AuthContext user — redirect happens via middleware
      // but we also push explicitly for SPA navigation
      const role = document.cookie.match(/utp_role=([^;]+)/)?.[1] ?? '';
      router.push(ROLE_REDIRECTS[role] ?? '/dashboard');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al iniciar sesión.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-center text-2xl">UTP Parking</CardTitle>
        <p className="text-center text-sm text-muted-foreground">Arequipa — Sótano 2 y 3</p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="codigo">Código Institucional</Label>
            <Input
              id="codigo"
              type="text"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="ALU001"
              autoComplete="username"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="password">Contraseña</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {fieldError && <p className="text-sm text-destructive">{fieldError}</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Ingresando...' : 'Ingresar'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Create `app/login/page.tsx`**

```typescript
import LoginForm from '@/components/LoginForm';

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <LoginForm />
    </main>
  );
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
npm run test -- LoginForm.test.tsx
```
Expected: PASS — 4 tests passed.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/LoginForm.tsx frontend/components/LoginForm.test.tsx frontend/app/login/page.tsx
git commit -m "feat: add login page with form validation and role-based redirect"
```

---

### Task 9: Route group layout skeletons

**Files:**
- Create: `frontend/app/(admin)/layout.tsx`
- Create: `frontend/app/(field)/layout.tsx`

These are skeletons — the full Sidebar and BottomNav are built in Plans 03 and 02 respectively.

- [ ] **Step 1: Create `app/(admin)/layout.tsx`**

```typescript
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar — implemented in Plan 03 */}
      <aside className="w-64 bg-white border-r border-slate-200 flex-shrink-0">
        <div className="p-4 font-semibold text-slate-800">UTP Parking</div>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Create `app/(field)/layout.tsx`**

```typescript
export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <main className="flex-1 overflow-auto">{children}</main>
      {/* BottomNav — implemented in Plan 02 */}
      <nav className="h-16 bg-white border-t border-slate-200" />
    </div>
  );
}
```

- [ ] **Step 3: Create placeholder pages so the app doesn't 404**

Create `frontend/app/(admin)/dashboard/page.tsx`:
```typescript
export default function DashboardPage() {
  return <div className="text-slate-600">Dashboard — implementado en Plan 03</div>;
}
```

Create `frontend/app/(field)/my-qr/page.tsx`:
```typescript
export default function MyQrPage() {
  return <div className="p-4 text-slate-600">Mi QR — implementado en Plan 02</div>;
}
```

- [ ] **Step 4: Verify dev server starts without errors**

```bash
npm run dev &
sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
```
Expected: `200`

- [ ] **Step 5: Commit**

```bash
git add frontend/app/
git commit -m "feat: add admin and field route group layout skeletons"
```

---

## Plan 01 complete

Run the full test suite to verify:
```bash
npm run test
```
Expected: All tests pass (auth + api + LoginForm).

The foundation is ready: Next.js app scaffolded, JWT auth implemented, Axios client with refresh, role-based middleware, and a working login page. Plans 02–05 implement the screens and offline features on top of this foundation.
