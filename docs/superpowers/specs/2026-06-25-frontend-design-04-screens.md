# Frontend Design — Módulo 04: Pantallas por Rol

**Fecha:** 2026-06-25

---

## Layout `(field)` — Mobile-first

### Bottom Navigation
Visible solo para roles field. Ítems visibles según rol:

| Ícono | Ruta | Visible para |
|---|---|---|
| QR scan | `/scan` | AGENTE |
| Mi QR | `/my-qr` | ALUMNO, DOCENTE, ADMINISTRATIVO, VISITANTE |
| Mi vehículo | `/my-vehicle` | ALUMNO, DOCENTE, ADMINISTRATIVO |
| Mis infracciones | `/my-violations` | ALUMNO, DOCENTE, ADMINISTRATIVO |

---

### `/scan` — Escáner QR (Agente)

**Componentes:**
- `QrScanner` — viewport de cámara a pantalla completa, overlay con guía de encuadre
- `ScanResult` — tarjeta con resultado del escaneo (verde/rojo/amarillo)
- `ScanHistory` — lista compacta de los últimos 10 escaneos del turno
- `OfflineBanner` — banner amarillo si >10 min sin conexión

**Estados del resultado:**

| Color | Mensaje | Cuándo |
|---|---|---|
| Verde | "ENTRADA REGISTRADA — [Nombre] · [Placa]" | 200 OK |
| Verde | "SALIDA REGISTRADA — [Nombre] · [Placa]" | 200 OK salida |
| Rojo | "ACCESO DENEGADO — [motivo]" | 403 (suspendido, sin reserva, etc.) |
| Rojo | "QR INVÁLIDO o EXPIRADO" | 400 token inválido |
| Amarillo | "REGISTRADO LOCALMENTE — sincronizará al recuperar señal" | Offline |

El resultado permanece visible 4 segundos y luego vuelve al estado de cámara activa automáticamente.

---

### `/my-qr` — QR Personal (Alumno, Docente, Admin, Visitante)

**Contenido:**
- QR grande centrado (generado con `qrcode.react` desde el token JWT del usuario)
- Nombre completo + código institucional
- Placa del vehículo registrado (o "Sin vehículo registrado" con link a `/my-vehicle`)
- Botón "Actualizar QR" — hace refresh del token si está próximo a expirar

**Nota:** El QR muestra el token de acceso QR especial (RS256, firmado por el backend, distinto al JWT de sesión). El backend provee `GET /api/v1/auth/qr-token/` para obtenerlo.

---

### `/my-vehicle` — Registro de Vehículo

**Formulario:**
- Placa (texto, validación formato peruano: ABC-123 o A1B-234)
- Tipo: MOTO / AUTO / CAMIONETA / OTRO (select)
- Marca (texto libre)
- Modelo (texto libre, opcional)
- Color (texto libre, opcional)

Si el usuario ya tiene vehículo registrado, muestra los datos actuales con botón Editar.

---

### `/my-violations` — Mis Infracciones

Lista de infracciones del usuario autenticado (`GET /api/v1/violations/my/`).

Cada ítem muestra:
- Tipo de falta y nivel (leve/grave/muy grave) — badge de color
- Fecha
- Estado: PENDIENTE / CONFIRMADA / ANULADA
- Si CONFIRMADA: tipo de sanción y duración

---

## Layout `(admin)` — Desktop-first

### Sidebar
- Logo UTP + "Parking Arequipa"
- Ítems de navegación visibles según rol (ver tabla de acceso abajo)
- Usuario actual + rol en la parte inferior
- Botón Cerrar sesión

**Ítems del sidebar por rol:**

| Ítem | AGENTE | JEFE_SEG | JEFE_OPS | DIRECTOR | RECTOR |
|---|---|---|---|---|---|
| Dashboard | — | ✓ | ✓ | ✓ | ✓ |
| Infracciones | ✓ | ✓ | ✓ | — | — |
| Reservas | — | — | ✓ | ✓ | — |
| Reportes | — | ✓ | ✓ | ✓ | ✓ |
| Espacios | — | — | — | ✓ | ✓ |
| Usuarios | — | — | — | ✓ | ✓ |

*Nota: AGENTE accede a la vista admin solo para gestión de infracciones.*

---

### `/dashboard` — Ocupación en Tiempo Real

**Polling:** `GET /api/v1/spaces/campus/{id}/occupancy/` cada 15 segundos via `useOccupancy` hook.

**Layout:**
```
┌─────────────────────┬─────────────────────┐
│   Sótano 2          │   Sótano 3          │
│   45/60 ocupados    │   12/40 ocupados    │
│   [====------]      │   [==--------]      │
│                     │                     │
│   Libres:    15     │   Libres:    28     │
│   Reservados: 2     │   Reservados: 0     │
└─────────────────────┴─────────────────────┘

Por tipo de espacio (tabla debajo de las tarjetas):
  ESTANDAR | DISCAPACITADO | MOTOCICLETA | VIP
  Total / Libres / Ocupados / Reservados
```

Indicador de última actualización: "Actualizado hace X seg".

---

### `/violations` — Gestión de Infracciones

**Para AGENTE y roles superiores.**

**Lista:** tabla con filtros por estado, nivel y fecha. Columnas: usuario, placa, tipo de falta, nivel, fecha, estado, acciones.

**Crear infracción** (botón superior derecho):
- Buscar usuario por código institucional o placa
- Seleccionar tipo de falta (dropdown con los 19 tipos del reglamento)
- Descripción opcional
- Al guardar: muestra la sanción propuesta calculada por el backend antes de confirmar

**Detalle `/violations/[id]`:**
- Datos completos de la infracción
- Sanción propuesta (si estado PENDIENTE)
- Botones: "Confirmar infracción" (Jefe Ops+) / "Anular" (Jefe Ops+)

---

### `/reservations` — Gestión de Reservas

**Para JEFE_OPERACIONES y DIRECTOR.**

**Vista:** lista de reservas activas con espacio, beneficiario, horario y estado.

**Crear reserva** (modal):
- Seleccionar espacio (solo del campus del usuario)
- Beneficiario (búsqueda por código o nombre, opcional)
- Fecha/hora inicio y fin
- Motivo

**Cancelar:** botón en cada fila, confirmación con dialog.

---

### `/reports` — Descarga de Reportes

**Para JEFE_SEGURIDAD, JEFE_OPERACIONES, DIRECTOR, RECTOR.**

Tres secciones (acordeón):

1. **Reporte de Ocupación**
   - Filtros: campus (Rector puede elegir), fecha desde, fecha hasta
   - Formato: xlsx / pdf
   - Botón "Descargar"

2. **Reporte de Infracciones**
   - Filtros: campus, fecha desde, fecha hasta
   - Formato: xlsx / pdf

3. **Reporte de Usuarios (HCM)**
   - Filtros: campus
   - Formato: xlsx / pdf
   - Solo visible para DIRECTOR y RECTOR

---

### `/spaces` — Gestión de Espacios

**Para DIRECTOR y RECTOR.**

Vista de espacios agrupados por sótano. Tabla con: código, tipo, estado, acciones (editar estado).

---

### `/users` — Gestión de Usuarios

**Para DIRECTOR y RECTOR.**

Lista paginada de usuarios del campus. Columnas: código, nombre, rol, estado, sanciones activas, vehículos registrados.

Filtros: por rol, por estado (ACTIVO / SUSPENDIDO / INACTIVO).

No incluye creación de usuarios (los usuarios se sincronizan desde el sistema HCM de UTP según el diseño del backend).
