# Frontend Design — Módulo 03: Offline Queue y PWA

**Fecha:** 2026-06-25

---

## Contexto

Los agentes operan en Sótano 2 y Sótano 3. La cobertura WiFi puede ser intermitente. El backend ya tiene un endpoint de sync batch (`POST /api/v1/access/sync/`) implementado en el Plan 03.

---

## Service Worker (next-pwa + Workbox)

`next.config.js`:

```javascript
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  runtimeCaching: [
    {
      urlPattern: /^https?.*\/api\/v1\/auth\//,
      handler: 'NetworkOnly', // auth siempre requiere red
    },
    {
      urlPattern: /^https?.*\/api\/v1\//,
      handler: 'NetworkFirst', // intenta red, cae a cache si falla
      options: { cacheName: 'api-cache', networkTimeoutSeconds: 5 },
    },
  ],
});
```

El service worker **no intercepta** los POST de acceso — eso lo maneja `offline-queue.ts` directamente desde la app para tener control total sobre el retry y la UI.

---

## `lib/offline-queue.ts` — Cola con Dexie.js

### Schema de IndexedDB

```typescript
interface PendingScan {
  id?: number;           // autoincrement
  qr_token: string;
  tipo: 'entry' | 'exit';
  timestamp: string;     // ISO 8601 — momento del escaneo
  intent: 'entry' | 'exit';
  retries: number;       // contador de intentos fallidos
  status: 'pending' | 'failed';
}
```

### Operaciones principales

```typescript
export async function enqueueScan(scan: Omit<PendingScan, 'id' | 'retries' | 'status'>)
export async function syncPending(): Promise<{ synced: number; failed: number }>
export async function getPendingCount(): Promise<number>
export async function clearFailed(): Promise<void>
```

### Lógica de sync

```
syncPending():
  1. Lee todos los registros con status === 'pending' ordenados por timestamp
  2. POST /api/v1/access/sync/ con el array de scans pendientes
  3. El backend procesa cada uno y devuelve resultados por id
  4. Para cada resultado:
     - exitoso → borra el registro de IndexedDB
     - token_expirado → marca status = 'failed' (no reintentable)
     - error_servidor → incrementa retries; si retries >= 3 → marca 'failed'
  5. Retorna { synced, failed }
```

---

## `hooks/useOfflineSync.ts`

```typescript
export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [offlineSince, setOfflineSince] = useState<Date | null>(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const handleOnline = async () => {
      setIsOnline(true);
      setOfflineSince(null);
      setShowBanner(false);
      await syncPending();
      setPendingCount(await getPendingCount());
    };
    const handleOffline = () => {
      setIsOnline(false);
      setOfflineSince(new Date());
    };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => { /* cleanup */ };
  }, []);

  // Timer de 10 minutos
  useEffect(() => {
    if (!offlineSince) return;
    const ms = 10 * 60 * 1000;
    const timer = setTimeout(() => setShowBanner(true), ms);
    return () => clearTimeout(timer);
  }, [offlineSince]);

  return { isOnline, pendingCount, showBanner };
}
```

---

## `components/shared/OfflineBanner.tsx`

Aparece cuando `showBanner === true`:

```
┌─────────────────────────────────────────────────────────┐
│ ⚠  Sin conexión hace más de 10 min                      │
│    3 registros pendientes de sincronizar                 │
│                              [Ver pendientes]            │
└─────────────────────────────────────────────────────────┘
```

- Banner fijo en la parte superior de la pantalla del agente
- Fondo amarillo (#FEF3C7) para visibilidad en condiciones de luz variable
- Desaparece automáticamente cuando el sync completa
- "Ver pendientes" abre un modal con la lista de scans en cola

---

## PWA Manifest (`public/manifest.json`)

```json
{
  "name": "UTP Parking",
  "short_name": "UTP Parking",
  "description": "Sistema de estacionamiento UTP Arequipa",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1e40af",
  "theme_color": "#1e40af",
  "orientation": "portrait",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

**Colores UTP:** azul institucional `#1e40af` como theme color. Los íconos se generan durante el setup del proyecto.

---

## Flujo completo del Agente — con y sin señal

### Con señal
```
/scan → cámara activa → usuario apunta QR del alumno
      → html5-qrcode decodifica token QR
      → POST /api/v1/access/entry/ { qr_token }
      → 200: muestra tarjeta verde con nombre + placa + "ENTRADA REGISTRADA"
      → 400/403: muestra tarjeta roja con motivo (suspendido, sin vehículo, etc.)
```

### Sin señal
```
/scan → cámara activa → decodifica token QR
      → navigator.onLine === false
      → enqueueScan({ qr_token, tipo: 'entry', timestamp: now })
      → muestra tarjeta amarilla "Registrado localmente — se sincronizará al recuperar señal"
      → incrementa contador de pendientes en UI
```

### Historial del turno
La pantalla `/scan` muestra los últimos 10 escaneos del turno actual (desde IndexedDB + respuestas en memoria) para que el agente tenga contexto inmediato sin necesidad de ir al admin.
