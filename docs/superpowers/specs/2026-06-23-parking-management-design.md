# Sistema de Gestión de Estacionamiento UTP — Diseño v1

**Fecha:** 2026-06-23
**Proyecto:** Control de Estacionamiento UTP
**Piloto:** Campus Arequipa (Sótano 2 y Sótano 3)
**Alcance:** v1 — Sistema operativo completo para un campus, escalable a nivel nacional

---

## 1. Contexto y objetivo

La Universidad Tecnológica del Perú (UTP) necesita un sistema digital para gestionar el acceso, ocupación y sanciones de sus estacionamientos. El piloto se realizará en el campus Arequipa (Av. Parra N° 201-203), que cuenta con dos sótanos de estacionamiento. El sistema reemplaza el proceso manual actual (tarjetas físicas, registros en papel) y sienta las bases para escalar a todos los campus a nivel nacional.

**Problema central:** El proceso actual depende de tarjetas físicas propensas a error y no deja trazabilidad digital de accesos, sanciones ni ocupación en tiempo real.

**Solución:** Aplicación web con PWA para agentes, control por QR firmado digitalmente, gestión de sanciones según el reglamento oficial (SEG-PT002), y reportes exportables a Excel/PDF.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend API | Django + Django REST Framework |
| Documentación API | drf-spectacular (Swagger UI / ReDoc) |
| Autenticación | djangorestframework-simplejwt (JWT) |
| Base de datos | PostgreSQL |
| Frontend | React + TypeScript + Tailwind CSS |
| App de agentes (offline) | PWA con Service Workers |
| QR offline | JWT firmado (RS256) embebido en QR |
| Exportar Excel/PDF | openpyxl + ReportLab |
| Auditoría | django-auditlog |
| Contenedores | Docker + docker-compose |

---

## 3. Arquitectura general

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENTES                            │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Web App     │  │  PWA Agente  │  │  Web App     │  │
│  │  (admin /    │  │  (entrada,   │  │  (usuario:   │  │
│  │   directivos)│  │   salida,    │  │   ver        │  │
│  │              │  │   rondas)    │  │   historial) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼─────────────────┼─────────────────┼───────────┘
          └─────────────────┼─────────────────┘
                            │ HTTPS / REST API
                    ┌───────▼────────┐
                    │   Django +     │
                    │   DRF          │
                    │                │
                    │  ┌──────────┐  │
                    │  │  auth    │  │
                    │  │  access  │  │
                    │  │  spaces  │  │
                    │  │violations│  │
                    │  │ reports  │  │
                    │  └──────────┘  │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  PostgreSQL    │
                    │  (multi-       │
                    │   campus)      │
                    └────────────────┘
```

**Decisiones clave:**
- Un solo backend sirve a todos los campus. El aislamiento es por `campus_id` en cada registro — no hay bases de datos separadas por sede.
- Tres interfaces según perfil: panel web para gestión, PWA para agentes en campo, vista simplificada para usuarios finales.
- La PWA del agente maneja salidas offline con cola de sincronización; las entradas siempre son online (se realizan en la calle con señal).
- Docker + docker-compose para despliegue reproducible en cualquier servidor o nube.

---

## 4. Modelo de datos

### Diagrama de relaciones

```
Campus ──< ParkingLot ──< ParkingSpace
  │                            │
  │                       Reservation
  │
  └──< User ──< Vehicle
         │          │
         │          └──< AccessRecord >── ParkingSpace
         │                    │
         └──< Violation ───────┘
                  │
              Sanction
```

### Entidades

**Campus**
Sede universitaria. Todos los datos se filtran por campus_id para aislamiento entre sedes.
- `id`, `nombre`, `ciudad`, `direccion`, `horario_operacion` (JSON por tipo de sede), `activo`

**ParkingLot**
Sótano o nivel de estacionamiento dentro de un campus.
- `id`, `campus` (FK), `nombre` (ej: "Sótano 2"), `nivel`

**ParkingSpace**
Espacio individual dentro de un sótano.
- `id`, `lot` (FK), `numero` (ej: "A-01"), `tipo` (auto/moto/bicicleta/discapacitado/reservado), `estado` (libre/ocupado/reservado)

**User**
Todos los roles del sistema en una sola tabla diferenciada por el campo `rol`.
- `id`, `codigo_institucional` (único), `email_institucional`, `nombre`, `apellido`, `rol`, `campus_asignado` (FK), `estado` (activo/suspendido/inactivo), `suspension_hasta` (date, nullable)

**Vehicle**
Vehículo registrado de un usuario. Máximo 2 por usuario.
- `id`, `user` (FK), `placa`, `tipo` (auto/moto/bicicleta), `marca`, `modelo`, `color`, `activo`

**AccessRecord**
Registro de cada entrada y salida vehicular.
- `id`, `user` (FK), `vehicle` (FK), `campus` (FK), `space` (FK), `entrada_at`, `salida_at` (nullable), `registrado_por` (FK User agente), `estado` (activo/completado)

**ViolationType**
Catálogo de tipos de falta precargado del reglamento SEG-PT002. 19 faltas en total.
- `id`, `codigo` (ej: "LEVE_E"), `descripcion`, `nivel` (leve/grave/muy_grave)

**Violation**
Falta levantada por un agente de seguridad o asistente de operaciones durante una ronda o al momento del acceso.
- `id`, `user` (FK), `vehicle` (FK), `campus` (FK), `tipo_falta` (FK ViolationType), `descripcion`, `evidencia_foto` (nullable), `registrado_por` (FK User), `fecha`, `access_record` (FK nullable), `estado` (pendiente/confirmada/anulada/apelada)

**Sanction**
Sanción calculada automáticamente en base al historial de reincidencias del usuario.
- `id`, `user` (FK), `violation` (FK), `tipo` (advertencia/suspension_temporal/suspension_definitiva), `inicio`, `fin` (nullable para definitiva), `aplicada_por` (FK User), `estado` (activa/cumplida/anulada/apelada)

**SanctionRule**
Tabla de configuración precargada del reglamento. Permite ajustar reglas sin tocar código.
- `nivel_falta`, `numero_reincidencia`, `tipo_sancion`, `duracion_meses` (nullable)

**Reservation**
Reserva de espacio exclusiva para Director y Jefe de Operaciones.
- `id`, `campus` (FK), `space` (FK), `reservado_por` (FK User), `descripcion_visita`, `fecha_inicio`, `fecha_fin`, `motivo`

---

## 5. Roles y permisos

### Jerarquía organizacional

```
Rector (nacional)
    └── Director (por campus)
            └── Jefe de Operaciones
                    ├── Jefe de Seguridad (consultivo)
                    └── Asistente de Operaciones
                              └── Agente de Seguridad

Usuarios finales: Administrativo · Académico · Alumno
```

### Tabla de permisos

**Nivel 0 — Superadmin nacional**

| Acción | Rector |
|---|:---:|
| Ver dashboards de todos los campus | ✅ |
| Gestionar usuarios y vehículos (cualquier campus) | ✅ |
| Confirmar / anular sanciones | ✅ |
| Configurar campus y espacios | ✅ |
| Importar / exportar Excel o PDF | ✅ |
| Reservar espacio (cualquier campus) | ✅ |
| Crear / desactivar cuentas de directores y jefes | ✅ |
| Ver reportes consolidados multi-campus | ✅ |

**Nivel 1 — Control por campus**

| Acción | Director | Jefe Operaciones | Jefe Seguridad |
|---|:---:|:---:|:---:|
| Ver todos los dashboards y reportes | ✅ | ✅ | ✅ |
| Gestionar usuarios y vehículos | ✅ | ✅ | ❌ |
| Confirmar / anular sanciones | ✅ | ✅ | ❌ |
| Configurar campus y espacios | ✅ | ✅ | ❌ |
| Importar / exportar Excel o PDF | ✅ | ✅ | ✅ |
| Reservar espacio (propio o visita) | ✅ | ✅ | ❌ |

**Nivel 2 — Operativo en campo**

| Acción | Agente Seguridad | Asistente Operaciones |
|---|:---:|:---:|
| Escanear QR (entrada / salida) | ✅ | ❌ |
| Ver disponibilidad de espacios | ✅ | ✅ |
| Registrar violación (ronda o acceso) | ✅ | ✅ |
| Ver datos del usuario al escanear | ✅ | ✅ |
| Editar usuarios / vehículos | ❌ | ❌ |
| Ver reportes globales | ❌ | ✅ |

**Nivel 3 — Usuario final**

| Acción | Alumno | Académico | Administrativo |
|---|:---:|:---:|:---:|
| Ver disponibilidad en tiempo real | ✅ | ✅ | ✅ |
| Ver propio historial entrada/salida | ✅ | ✅ | ✅ |
| Ver propias faltas y sanciones | ✅ | ✅ | ✅ |
| Ver datos de otros usuarios | ❌ | ❌ | ❌ |

**Reglas transversales:**
- Cada usuario solo ve datos de su campus asignado. Solo el Rector y el Director tienen visibilidad ampliada.
- Un usuario con sanción activa es bloqueado automáticamente al escanear su QR en entrada.

---

## 6. Flujos principales

### Flujo 1 — Entrada vehicular (siempre online)

```
Usuario muestra QR
        │
Agente escanea con PWA
        │
Sistema valida:
  ├── JWT válido y no expirado
  ├── Usuario activo y autorizado
  ├── Sin suspensión activa
  ├── Vehículo registrado
  └── Campus correcto
        │
   ┌────┴────┐
  PASA     BLOQUEADO
    │           │
    ▼           ▼
Agente      Agente ve motivo
asigna      exacto del bloqueo
espacio
    │
    ▼
AccessRecord creado (entrada_at)
Espacio → ocupado
```

### Flujo 2 — Salida vehicular (soporta offline en sótano)

```
Usuario muestra QR
        │
Agente escanea con PWA
        │
   ┌────┴────┐
CON SEÑAL   SIN SEÑAL
    │            │
    ▼            ▼
Cierra      Cola local:
AccessRecord  salida_at + espacio
en tiempo   (sync al subir rampa)
real
```

Alerta automática si el vehículo lleva más de 15 minutos sin moverse (regla del reglamento).

### Flujo 3 — Registro de violación

```
Agente o Asistente de Operaciones
escanea QR o busca por placa
        │
Ve datos del usuario + historial de faltas
        │
Selecciona tipo de falta del catálogo
Agrega descripción + foto (opcional)
        │
Sistema crea Violation (pendiente)
Sistema calcula sanción propuesta según SanctionRule
        │
Notifica a Jefe de Operaciones
        │
Jefe de Operaciones revisa → confirma o anula
        │
Si confirma → Sanction activa → acceso bloqueado si aplica
```

### Flujo 4 — Reserva de espacio

```
Director o Jefe de Operaciones
selecciona campus → ve mapa de espacios
        │
Elige espacio + rango fecha/hora + motivo
(propio uso o visita importante)
        │
Sistema verifica disponibilidad en rango
        │
Crea Reservation → espacio reservado
(agente no puede asignarlo durante ese período)
```

---

## 7. Mecanismo QR offline

### Estructura del QR

El QR contiene un JWT firmado con RS256 (clave privada en el servidor):

```json
{
  "user_id": "U-001",
  "vehicle_id": "V-002",
  "campus_id": "C-AQP",
  "issued_at": "2026-06-23T08:30:00",
  "exp": "2026-06-23T08:35:00"
}
```

### Protecciones

- **Expira en 5 minutos** — QR capturado no reutilizable
- **Un solo uso por ventana** — el servidor rechaza `issued_at` ya procesado (previene replay attacks)
- **Firmado RS256** — clave privada solo en servidor, PWA solo tiene la pública para verificar

### Comportamiento por zona

| Zona | Señal | Mecanismo |
|---|---|---|
| Entrada (calle) | Siempre disponible | Validación completa online en tiempo real |
| Salida (sótano) | Inestable o sin señal | PWA valida JWT localmente, cola de sync al recuperar señal |

---

## 8. Seguridad del sistema

**Autenticación:**
- Login con código institucional + contraseña (bcrypt)
- JWT de sesión (15 min) + refresh token rotativo (7 días)
- Refresh tokens rotativos — cada uso genera uno nuevo e invalida el anterior

**Autorización:**
- Cada endpoint verifica rol + campus del usuario autenticado
- Un agente de Arequipa no puede operar en Lima aunque tenga token válido

**Datos sensibles:**
- Contraseñas almacenadas con bcrypt (nunca en texto plano)
- Comunicación exclusivamente por HTTPS
- Variables de entorno para secrets (nunca en código)
- Datos PII (DNI, placa) enmascarados en logs

**Auditoría:**
- django-auditlog registra quién cambió qué y cuándo en todos los modelos críticos
- Los logs de auditoría son de solo lectura — ningún rol puede borrarlos o modificarlos

---

## 9. Reportes y exportaciones

**Reporte 1 — Ocupación en tiempo real**
- Espacios libres / ocupados / reservados por campus y sótano
- Tiempo promedio de estancia del día
- Usuarios actualmente dentro del estacionamiento
- Disponible para todos los roles operativos y usuarios finales

**Reporte 2 — Historial de accesos**
- Entradas y salidas por rango de fechas
- Filtrable por usuario, placa, campus, espacio
- Exportable en formato compatible con Oracle Cloud HCM
- Nivel 1 y Nivel 2 ven todo; usuarios finales solo el propio

**Reporte 3 — Sanciones e infracciones**
- Violaciones por tipo de falta, campus y período
- Sanciones activas con fecha de vencimiento
- Historial de reincidencias por usuario
- Usuarios con suspensión activa o próxima a activarse
- Rector y Director ven global; Jefe Operaciones ve su campus; Jefe Seguridad solo lectura

**Formatos de exportación:**

| Formato | Librería | Uso |
|---|---|---|
| Excel (.xlsx) | openpyxl | Importar a Oracle Cloud HCM, análisis |
| PDF | ReportLab | Reportes formales, constancias de sanción |

---

## 10. Manejo de errores y casos borde

### Entrada / salida

| Situación | Comportamiento |
|---|---|
| QR expirado o sin QR | Búsqueda manual por código institucional o placa |
| Suspensión activa | Bloqueo con mensaje: "Suspendido hasta DD/MM/YYYY — Motivo: [falta]" |
| Vehículo no registrado | Bloqueo — escala a Asistente de Operaciones |
| Campus incorrecto | Alerta — excepción manual con justificación registrada |
| Sin espacios libres | Lista de espera visible para el agente |
| AccessRecord sin salida tras 24h | Alerta automática al Jefe de Operaciones |
| Espacio reservado asignado por error | Sistema bloquea y muestra titular y duración de reserva |

### Violaciones y sanciones

| Situación | Comportamiento |
|---|---|
| Violación por error | Jefe de Operaciones la anula antes de confirmar |
| Usuario apela sanción | Estado "apelada" — acceso no bloqueado durante revisión |
| Sanción vencida | Cron job diario reactiva el acceso automáticamente |
| Faltas de distintos niveles | Cada nivel tiene contador de reincidencias independiente |
| Sanción definitiva | Solo el Rector puede revertirla |

### Offline (solo salidas)

| Situación | Comportamiento |
|---|---|
| Salida sin internet | Cola local en PWA — sync automático al recuperar señal |
| Conflicto de sync (espacio asignado dos veces) | Primer registro gana — segundo queda en "conflicto" y alerta al Jefe de Operaciones |
| Cola de sync visible | Dashboard muestra salidas pendientes con marca de tiempo |

### Reglas de negocio críticas

- Máximo 2 vehículos por usuario — el sistema bloquea el intento de registrar un tercero
- Un usuario solo puede tener 1 AccessRecord activo simultáneamente
- Autorizaciones de docentes expiran al fin del ciclo académico (cron job automático)
- Autorizaciones de administrativos expiran anualmente (cron job automático)
- Ningún vehículo puede pernoctar más de 1 noche sin autorización previa

---

## 11. Testing y criterios de aceptación

### Estrategia de testing

```
E2E (Playwright)          — flujos dorados completos
Integration (pytest+DRF)  — endpoints API con BD real
Unit (pytest)             — lógica de negocio aislada
```

**Unit tests — lógica crítica:**
- Cálculo de sanción por nivel y número de reincidencias
- Expiración de autorizaciones (docente / administrativo)
- Validación de JWT del QR (firma, expiración, campus)
- Regla de máximo 2 vehículos por usuario

**Integration tests:**
- Entrada exitosa → AccessRecord creado → espacio ocupado
- Salida exitosa → AccessRecord cerrado → espacio libre
- Entrada bloqueada (suspendido, vehículo no registrado, campus incorrecto)
- Violación registrada → sanción calculada correcta → estado pendiente
- Reserva activa bloquea asignación del espacio

**E2E:**
- Agente escanea QR → usuario entra → espacio asignado
- Salida offline → sincroniza al reconectar
- Jefe de Operaciones aprueba sanción → usuario bloqueado en siguiente entrada

### Criterios de aceptación para el piloto

| Criterio | Verificación |
|---|---|
| Registro de entrada en menos de 10 segundos | Prueba cronometrada en caseta |
| QR de salida funciona sin señal en sótano | Prueba en campo con modo avión |
| Sanción calculada correctamente según reglamento | Casos de prueba con cada tipo de falta y reincidencia |
| Usuario suspendido no puede ingresar | Intento de entrada con sanción activa |
| Datos de un campus no visibles desde otro | Login con usuario de campus diferente |
| Exportación compatible con Oracle Cloud HCM | Importación de prueba en HCM staging |
| Panel accesible en tablet del agente | Prueba en dispositivo real en campo |

---

## 12. Catálogo de faltas (Reglamento SEG-PT002)

### Faltas Leves
| Código | Descripción |
|---|---|
| LEVE_A | No acatar indicaciones del personal de Seguridad |
| LEVE_B | No respetar turno solicitado o sede asignada |
| LEVE_C | No permitir revisión del vehículo |
| LEVE_D | Tocar bocina sin motivo urgente |
| LEVE_E | Estacionarse incorrectamente o invadir otro espacio |
| LEVE_F | No respetar espacios reservados para directivos |
| LEVE_G | Mantener ocupante en el vehículo una vez estacionado |
| LEVE_H | No usar luces dentro del estacionamiento |
| LEVE_I | Bloquear entrada esperando espacio disponible |
| LEVE_J | No respetar señales de tránsito internas |
| LEVE_K | Estacionar moto o bicicleta en espacio incorrecto |

### Faltas Graves
| Código | Descripción |
|---|---|
| GRAVE_A | No respetar zonas para personas con discapacidad |
| GRAVE_B | No estacionar según tipo de vehículo |
| GRAVE_C | Exceder velocidad de 10 km/h |
| GRAVE_D | Realizar maniobras temerarias |
| GRAVE_E | Vehículo pernoctando sin autorización |
| GRAVE_F | Agredir física o verbalmente al personal |

### Faltas Muy Graves
| Código | Descripción |
|---|---|
| MUY_GRAVE_G | Prestar o usar Fotocheck ajeno |
| MUY_GRAVE_H | Modificar o adulterar el Fotocheck |

### Tabla de sanciones

| Nivel | 1ª vez | 2ª vez | 3ª vez |
|---|---|---|---|
| Leve | Email de advertencia | Suspensión 1 mes | Suspensión 3 meses |
| Grave | Suspensión 3 meses | Suspensión 6 meses | Suspensión 12 meses |
| Muy Grave | Suspensión 12 meses | Suspensión 24 meses | Suspensión definitiva |

---

## 13. Escalabilidad y hoja de ruta

### v1 — Piloto Arequipa
Sistema completo operativo para un campus. Monolito modular con dominios bien delimitados.

### v2 — Despliegue nacional
Activación de multi-tenancy completo. El mismo sistema sirve todos los campus con `campus_id`. Sin cambios de arquitectura.

### v3 — Integración de cámaras
Módulo de reconocimiento de placas (OCR/LPR) que reemplaza el QR en entradas. Las interfaces internas ya están preparadas para recibir el `vehicle_id` desde cualquier fuente.

### v4 — Microservicios si se requiere
Si la carga lo justifica, los módulos del monolito (access, violations, spaces, reports) tienen fronteras claras para extraerse como servicios independientes sin reescribir la lógica de negocio.
