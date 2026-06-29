"""
Script de importación de datos para UTP Arequipa.
Ejecutar con: docker compose exec web python scripts/import_data.py
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import openpyxl
from django.db import transaction
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType
from apps.users.models import User, Vehicle, Role, VehicleType

# ─────────────────────────────────────────────
# 1. CAMPUS + ESTACIONAMIENTOS
# ─────────────────────────────────────────────
print("\n=== Creando campus UTP Arequipa ===")

campus, created = Campus.objects.get_or_create(
    nombre="UTP Arequipa",
    defaults={
        "ciudad": "Arequipa",
        "direccion": "Esquina Av. Parra N° 201-203 con Av. Andrés Martínez N° 101",
        "horario_operacion": {
            "lunes_sabado": {"inicio": "07:00", "fin": "22:00"},
            "domingo": {"inicio": "08:00", "fin": "14:00"},
        },
        "activo": True,
    }
)
print(f"  Campus: {'creado' if created else 'ya existía'} — {campus.nombre}")

# Sótano 2
s2, _ = ParkingLot.objects.get_or_create(
    campus=campus, nombre="Sótano 2", defaults={"nivel": -2}
)
# Sótano 3
s3, _ = ParkingLot.objects.get_or_create(
    campus=campus, nombre="Sótano 3", defaults={"nivel": -3}
)

def create_spaces(lot, specs):
    """specs: list of (prefix, tipo, count)"""
    created = 0
    for prefix, tipo, count in specs:
        for i in range(1, count + 1):
            numero = f"{prefix}-{i:02d}"
            _, c = ParkingSpace.objects.get_or_create(lot=lot, numero=numero, defaults={"tipo": tipo})
            if c:
                created += 1
    return created

print("\n=== Creando espacios Sótano 2 ===")
n = create_spaces(s2, [
    ("A", SpaceType.AUTO, 59),
    ("D", SpaceType.DISCAPACITADO, 2),
    ("M", SpaceType.MOTO, 12),
    ("B", SpaceType.BICICLETA, 20),
])
print(f"  Sótano 2: {n} espacios creados (total configurados: {ParkingSpace.objects.filter(lot=s2).count()})")

print("\n=== Creando espacios Sótano 3 ===")
n = create_spaces(s3, [
    ("A", SpaceType.AUTO, 107),
    ("D", SpaceType.DISCAPACITADO, 1),
    ("M", SpaceType.MOTO, 21),
    ("B", SpaceType.BICICLETA, 15),
])
print(f"  Sótano 3: {n} espacios creados (total configurados: {ParkingSpace.objects.filter(lot=s3).count()})")

# ─────────────────────────────────────────────
# 2. USUARIOS + VEHÍCULOS
# ─────────────────────────────────────────────
print("\n=== Importando usuarios AREQU ===")

ROL_MAP = {
    "Alumno": Role.ALUMNO,
    "Docente": Role.ACADEMICO,
    "Administrativo": Role.ADMINISTRATIVO,
}

TIPO_VEHICULO_MAP = {
    "Auto": VehicleType.AUTO,
    "Camioneta": VehicleType.AUTO,
    "Motocicleta": VehicleType.MOTO,
    "Moto eléctrica": VehicleType.MOTO,
}

def parse_codigo(email):
    """Deriva codigo_institucional desde el email."""
    prefix = email.split("@")[0]
    # u18217347 → 18217347 (alumnos con prefijo 'u')
    if prefix.startswith("u") and prefix[1:].isdigit():
        return prefix[1:]
    return prefix

def split_nombre_apellido(full_name):
    parts = full_name.strip().split()
    if len(parts) >= 4:
        return " ".join(parts[:2]), " ".join(parts[2:])
    elif len(parts) == 3:
        return parts[0], " ".join(parts[1:])
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        return full_name, ""

def parse_vehicles(vehiculo_str):
    """'Auto: VBO-159 | Camioneta: VDM-202' → [(tipo, placa), ...]"""
    if not vehiculo_str:
        return []
    result = []
    for part in str(vehiculo_str).split("|"):
        part = part.strip()
        if ":" not in part:
            continue
        tipo_str, placa = part.split(":", 1)
        tipo_str = tipo_str.strip()
        placa = placa.strip()
        tipo = TIPO_VEHICULO_MAP.get(tipo_str, VehicleType.AUTO)
        if placa:
            result.append((tipo, placa))
    return result[:2]  # máximo 2

wb = openpyxl.load_workbook("/app/Documentos estacionamientos/BD usuarios estacionamiento.xlsx")
ws = wb.active

stats = {"usuarios_creados": 0, "usuarios_omitidos": 0, "vehiculos_creados": 0, "errores": 0}
seen_emails = set()
seen_codigos = set()

with transaction.atomic():
    for row in ws.iter_rows(min_row=2, values_only=True):
        sede = row[6]
        if not sede or "AREQU" not in str(sede):
            continue

        email = (row[7] or "").strip().lower()
        if not email:
            stats["errores"] += 1
            continue

        # Saltar duplicados en el Excel
        if email in seen_emails:
            stats["usuarios_omitidos"] += 1
            continue
        seen_emails.add(email)

        categoria = row[8] or ""
        rol = ROL_MAP.get(categoria)
        if not rol:
            stats["errores"] += 1
            continue

        full_name = (row[1] or "").strip()
        dni = str(row[2] or "").strip()
        vehiculo_str = row[10]

        codigo = parse_codigo(email)
        # Si el código ya existe, añadir sufijo del DNI para evitar colisiones
        if codigo in seen_codigos:
            codigo = f"{codigo}_{dni[-4:]}" if dni else f"{codigo}_x"
        seen_codigos.add(codigo)

        nombre, apellido = split_nombre_apellido(full_name)

        # Crear usuario si no existe (por email)
        user = None
        try:
            user = User.objects.get(email=email)
            stats["usuarios_omitidos"] += 1
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(
                    codigo_institucional=codigo,
                    email=email,
                    password=dni if dni else "utp2026",
                    nombre=nombre,
                    apellido=apellido,
                    rol=rol,
                    campus_asignado=campus,
                )
                stats["usuarios_creados"] += 1
            except Exception as e:
                stats["errores"] += 1
                # print(f"  ERROR usuario {email}: {e}")
                continue

        if user is None:
            continue

        # Crear vehículos
        for tipo_v, placa in parse_vehicles(vehiculo_str):
            try:
                _, vc = Vehicle.objects.get_or_create(placa=placa, defaults={"user": user, "tipo": tipo_v})
                if vc:
                    stats["vehiculos_creados"] += 1
            except Exception:
                pass  # placa duplicada en otro usuario

print(f"\n  Usuarios creados:   {stats['usuarios_creados']}")
print(f"  Usuarios omitidos:  {stats['usuarios_omitidos']} (ya existían o duplicados en Excel)")
print(f"  Vehículos creados:  {stats['vehiculos_creados']}")
print(f"  Errores:            {stats['errores']}")

print("\n=== Resumen final ===")
print(f"  Total usuarios en BD:   {User.objects.exclude(is_superuser=True).count()}")
print(f"  Total vehículos en BD:  {Vehicle.objects.count()}")
print(f"  Espacios Sótano 2:      {ParkingSpace.objects.filter(lot=s2).count()}")
print(f"  Espacios Sótano 3:      {ParkingSpace.objects.filter(lot=s3).count()}")
print("\n¡Importación completada!")
