# Frontend Design — Módulo 05: Testing y Consideraciones Finales

**Fecha:** 2026-06-25

---

## Estrategia de testing

### Unit tests (Vitest)

Cubren lógica pura sin DOM:

| Archivo | Qué se testea |
|---|---|
| `lib/offline-queue.test.ts` | enqueue, sync, getPendingCount, clearFailed |
| `lib/auth.test.ts` | setAccessToken, getAccessToken, clearAccessToken |
| `lib/api.test.ts` | interceptor de refresh en 401 |
| `hooks/useOfflineSync.test.ts` | timer de 10 min, eventos online/offline |

### Component tests (React Testing Library)

Cubren formularios e interacciones críticas:

| Componente | Casos |
|---|---|
| `LoginForm` | submit exitoso, error de credenciales, campo vacío |
| `VehicleForm` | validación de placa peruana, submit, edición |
| `ViolationCreateForm` | búsqueda de usuario, selección de tipo, sanción propuesta |
| `OfflineBanner` | aparece con showBanner=true, desaparece al sincronizar |
| `ScanResult` | renderiza verde/rojo/amarillo según prop |

### E2E (Playwright)

Flujos críticos contra el backend real (Docker compose up):

| Test | Pasos |
|---|---|
| `login-redirect.spec.ts` | Login como Agente → redirige a /scan; Login como Alumno → redirige a /my-qr; Login como Director → redirige a /dashboard |
| `scan-online.spec.ts` | Agente en /scan → simula QR válido → verifica tarjeta verde |
| `report-download.spec.ts` | Director en /reports → descarga xlsx de usuarios → verifica que el archivo se descarga |
| `violation-create.spec.ts` | Agente crea infracción → Jefe Ops confirma → estado cambia a CONFIRMADA |

---

## Variables de entorno

```bash
# .env.local (no commitear)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# .env.production
NEXT_PUBLIC_API_URL=https://api.parking.utp.edu.pe/api/v1
```

---

## Scripts npm

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "types:api": "openapi-typescript $NEXT_PUBLIC_API_URL/schema/ -o lib/api.types.ts",
    "lint": "next lint"
  }
}
```

---

## Consideraciones para producción (fuera del scope del piloto)

Documentadas aquí para referencia futura, **no se implementan en el piloto**:

- **HTTPS obligatorio** — el `httpOnly cookie` con `secure: true` requiere HTTPS
- **CORS** — el backend Django ya tiene `CORS_ALLOWED_ORIGINS` configurable
- **CDN para assets** — íconos PWA, JS chunks
- **Rate limiting en el proxy** `/api/auth/token` — previene abuso del endpoint de refresh
- **Monitoring** — Sentry para errores de frontend en producción
- **Tests de accesibilidad** — axe-playwright para cumplir estándares universitarios
- **i18n** — no aplica (todo en español)

---

## Resumen del alcance del piloto

### Incluido
- Next.js 14 App Router con route groups `(admin)` y `(field)`
- Auth con JWT + refresh en httpOnly cookie
- PWA instalable con service worker
- Cola offline con IndexedDB + sync batch
- Banner de 10 min sin conexión
- Escáner QR via cámara del browser
- Dashboard de ocupación con polling 15s
- CRUD de infracciones + confirmación/anulación
- Gestión de reservas
- Descarga de reportes (xlsx/pdf)
- Vista de espacios y usuarios (read + edición básica)
- QR personal para alumnos/docentes
- Registro de vehículo
- Vista de infracciones propias

### Fuera del alcance del piloto
- Notificaciones push (Web Push API)
- Chat o mensajería interna
- Creación de usuarios desde el frontend (viene de HCM)
- Dashboard multi-campus para Rector (ve un campus a la vez en el piloto)
- Modo oscuro
- App nativa (Android/iOS)

---

## Archivos de este spec

| Módulo | Archivo |
|---|---|
| 01 — Arquitectura | `2026-06-25-frontend-design-01-architecture.md` |
| 02 — Auth y API | `2026-06-25-frontend-design-02-auth-api.md` |
| 03 — Offline y PWA | `2026-06-25-frontend-design-03-offline-pwa.md` |
| 04 — Pantallas | `2026-06-25-frontend-design-04-screens.md` |
| 05 — Testing | `2026-06-25-frontend-design-05-testing.md` (este archivo) |
