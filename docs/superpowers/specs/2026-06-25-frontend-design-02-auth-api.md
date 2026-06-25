# Frontend Design — Módulo 02: Auth y API Client

**Fecha:** 2026-06-25

---

## JWT Flow

### Login

```
1. Usuario POST /api/v1/auth/login/ con { codigo_institucional, password }
2. Backend responde { access, refresh }
3. Frontend guarda:
   - access token → variable React en memoria (AuthContext)
   - refresh token → POST /api/auth/token (proxy Next.js) → httpOnly cookie
4. Lee rol del payload JWT → redirige a ruta correspondiente
```

El `access` token **nunca** se guarda en `localStorage` ni en ningún storage persistente. Vive solo en memoria mientras la sesión está activa.

### Refresh automático

`lib/api.ts` configura un interceptor Axios en respuestas:

```
Si response.status === 401:
  → POST /api/v1/auth/token/refresh/ con el cookie httpOnly (enviado automáticamente)
  → Si exitoso: actualiza access token en memoria, reintenta la request original
  → Si falla (refresh expirado): logout, redirige a /login
```

### Logout

```
1. POST /api/v1/auth/logout/ { refresh } → blacklist en backend
2. DELETE cookie via proxy /api/auth/token
3. Limpia AuthContext (access token en memoria)
4. Redirige a /login
```

---

## `lib/api.ts` — Axios instance

```typescript
// Configuración central
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL, // http://localhost:8000/api/v1
  withCredentials: true,                    // envía httpOnly cookie automáticamente
});

// Request interceptor: adjunta access token
api.interceptors.request.use((config) => {
  const token = getAccessToken(); // desde AuthContext
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: refresh automático en 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      await refreshToken();
      return api(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## `lib/auth.ts` — Gestión de tokens

```typescript
// access token vive en módulo-scope (memoria)
let _accessToken: string | null = null;

export const setAccessToken = (token: string) => { _accessToken = token; };
export const getAccessToken = () => _accessToken;
export const clearAccessToken = () => { _accessToken = null; };

export async function refreshToken(): Promise<void> {
  // El cookie httpOnly se envía automáticamente por withCredentials
  const res = await axios.post('/api/v1/auth/token/refresh/');
  setAccessToken(res.data.access);
}
```

---

## `app/api/auth/token/route.ts` — Proxy Next.js

Route handler de Next.js que recibe el refresh token y lo setea como `httpOnly cookie`:

```
POST /api/auth/token  → setea cookie httpOnly con el refresh token
DELETE /api/auth/token → borra el cookie (logout)
```

El cookie se configura con:
- `httpOnly: true` — inaccesible desde JavaScript del browser
- `secure: true` en producción
- `sameSite: 'lax'`
- `maxAge`: igual al tiempo de vida del refresh token del backend (configurable)

---

## Tipos desde OpenAPI

Al arrancar el proyecto (o en CI), se genera `lib/api.types.ts`:

```bash
npx openapi-typescript http://localhost:8000/api/v1/schema/ -o lib/api.types.ts
```

Esto provee tipos TypeScript para todos los request/response bodies del backend. Si el backend cambia un campo, TypeScript rompe en compilación antes de llegar a runtime.

Los hooks de TanStack Query usan estos tipos directamente:

```typescript
import type { components } from '@/lib/api.types';
type Violation = components['schemas']['Violation'];
```

---

## Manejo de errores por tipo

| Error | Comportamiento UI |
|---|---|
| Sin conexión (network error) | Toast: "Sin conexión — reintentando…" |
| 400 Bad Request | Errores inline en formulario (campo por campo) |
| 401 Unauthorized | Refresh automático → si falla, logout + redirect /login |
| 403 Forbidden | Pantalla "No tienes permiso" con botón volver |
| 404 Not Found | Pantalla "Recurso no encontrado" |
| 500 Server Error | Pantalla error genérica con mensaje de referencia |

Los errores 400 del backend tienen la forma `{ field: ["mensaje"] }` o `{ detail: "mensaje" }`. El componente de formulario lee ambos formatos y muestra el mensaje bajo el campo correspondiente.
