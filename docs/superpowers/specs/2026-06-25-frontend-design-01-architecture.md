# Frontend Design — Módulo 01: Arquitectura General

**Fecha:** 2026-06-25  
**Proyecto:** Sistema de Estacionamiento UTP — Arequipa (Sótano 2 y Sótano 3)  
**Alcance:** Frontend web + PWA para el piloto

---

## Stack tecnológico

| Tecnología | Versión | Rol |
|---|---|---|
| Next.js | 14 (App Router) | Framework principal, SSR + routing |
| TypeScript | 5.x strict | Tipado, contrato con API |
| Tailwind CSS | 3.x | Estilos utilitarios |
| shadcn/ui | latest | Componentes accesibles base |
| TanStack Query | v5 | Estado del servidor, cache, retry |
| Axios | 1.x | HTTP client con interceptores JWT |
| next-pwa + Workbox | latest | Service worker, offline support |
| Dexie.js | 3.x | IndexedDB wrapper para cola offline |
| html5-qrcode | 2.x | Escáner QR via cámara del browser |
| openapi-typescript | latest | Genera tipos desde `/api/v1/schema/` |
| Vitest | 1.x | Unit y component tests |
| React Testing Library | 14.x | Component tests |
| Playwright | 1.x | E2E tests |

---

## Estructura de carpetas

```
frontend/
├── app/
│   ├── (admin)/                  # Route group — Desktop-first
│   │   ├── layout.tsx            # Sidebar + topbar
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Ocupación en tiempo real
│   │   ├── violations/
│   │   │   ├── page.tsx          # Listado de infracciones
│   │   │   └── [id]/page.tsx     # Detalle / confirmar / anular
│   │   ├── reservations/
│   │   │   └── page.tsx          # Gestión de reservas
│   │   ├── reports/
│   │   │   └── page.tsx          # Descarga de reportes
│   │   ├── spaces/
│   │   │   └── page.tsx          # Gestión de espacios
│   │   └── users/
│   │       └── page.tsx          # Gestión de usuarios
│   ├── (field)/                  # Route group — Mobile-first PWA
│   │   ├── layout.tsx            # Bottom navigation
│   │   ├── scan/
│   │   │   └── page.tsx          # Escáner QR (solo Agente)
│   │   ├── my-qr/
│   │   │   └── page.tsx          # QR personal del usuario
│   │   ├── my-vehicle/
│   │   │   └── page.tsx          # Registro / edición de vehículo
│   │   └── my-violations/
│   │       └── page.tsx          # Mis infracciones propias
│   ├── login/
│   │   └── page.tsx              # Login compartido
│   ├── api/
│   │   └── auth/
│   │       └── token/
│   │           └── route.ts      # Proxy Next.js para httpOnly cookie
│   ├── layout.tsx                # Root layout — QueryClientProvider, AuthProvider
│   └── middleware.ts             # Protección de rutas por rol
├── lib/
│   ├── api.ts                    # Axios instance + interceptores JWT
│   ├── auth.ts                   # Token storage, refresh, logout
│   ├── offline-queue.ts          # IndexedDB cola + sync logic
│   └── api.types.ts              # Auto-generado desde OpenAPI schema
├── hooks/
│   ├── useAuth.ts
│   ├── useOccupancy.ts           # Polling 15s al dashboard
│   ├── useScan.ts                # Lógica del escáner QR
│   └── useOfflineSync.ts         # Estado de sincronización pending
├── components/
│   ├── ui/                       # shadcn/ui re-exports
│   ├── shared/                   # Compartidos entre admin y field
│   │   ├── OfflineBanner.tsx     # Banner de 10 min sin conexión
│   │   └── ErrorBoundary.tsx
│   ├── admin/                    # Exclusivos del layout admin
│   │   ├── Sidebar.tsx
│   │   ├── OccupancyCard.tsx
│   │   └── ViolationTable.tsx
│   └── field/                    # Exclusivos del layout field
│       ├── QrScanner.tsx
│       ├── QrDisplay.tsx
│       └── BottomNav.tsx
├── public/
│   ├── manifest.json             # PWA manifest
│   └── icons/                   # Íconos PWA (192x192, 512x512)
├── next.config.js                # next-pwa config
├── tailwind.config.js
└── tsconfig.json                 # strict: true
```

---

## Redirección por rol al login

El campo `rol` viene en el payload del JWT. Inmediatamente después del login exitoso:

| Rol | Destino |
|---|---|
| `AGENTE` | `/scan` |
| `ALUMNO`, `DOCENTE`, `ADMINISTRATIVO`, `VISITANTE` | `/my-qr` |
| `JEFE_OPERACIONES`, `JEFE_SEGURIDAD`, `DIRECTOR`, `RECTOR` | `/dashboard` |

---

## Protección de rutas — `middleware.ts`

El middleware de Next.js intercepta todas las requests a rutas protegidas:

1. Lee el `refresh` cookie — si no existe → redirige a `/login`
2. Lee el rol del JWT payload
3. Si la ruta es `(admin)/*` y el rol es `AGENTE`, `ALUMNO`, `DOCENTE`, `ADMINISTRATIVO` o `VISITANTE` → redirige a la ruta field correcta
4. Si la ruta es `(field)/scan` y el rol no es `AGENTE` → redirige a `/my-qr`

El middleware **no valida el token contra el backend** — eso lo hace Axios en cada API call. El middleware solo hace routing básico por rol para UX, la seguridad real está en el backend.
