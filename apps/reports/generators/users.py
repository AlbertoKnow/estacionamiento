from django.http import HttpResponse

from apps.users.models import User
from apps.violations.models import SanctionState


def _queryset(campus_id: int):
    return User.objects.filter(
        campus_asignado_id=campus_id
    ).prefetch_related('vehicles', 'sanctions')


def _headers():
    return [
        'codigo_institucional', 'nombre', 'apellido', 'email',
        'rol', 'campus', 'estado', 'sanciones_activas', 'vehiculos',
    ]


def _rows(users):
    rows = []
    for u in users:
        sanciones_activas = sum(
            1 for s in u.sanctions.all() if s.estado == SanctionState.ACTIVA
        )
        placas = ', '.join(v.placa for v in u.vehicles.filter(activo=True))
        rows.append([
            u.codigo_institucional,
            u.nombre,
            u.apellido,
            u.email,
            u.rol,
            u.campus_asignado.nombre if u.campus_asignado else '',
            u.estado,
            sanciones_activas,
            placas,
        ])
    return rows


def generate_users_report(campus_id: int, fmt: str) -> HttpResponse:
    from apps.reports.generators.occupancy import _to_xlsx, _to_pdf
    users = _queryset(campus_id)
    headers = _headers()
    rows = _rows(users)
    filename = f'usuarios_campus_{campus_id}'
    if fmt == 'xlsx':
        return _to_xlsx(headers, rows, filename)
    return _to_pdf(headers, rows, f'Reporte de Usuarios — Campus {campus_id}', filename)
