from datetime import date
from django.http import HttpResponse

from apps.violations.models import Violation


def _queryset(campus_id: int, date_from: date, date_to: date):
    return Violation.objects.filter(
        campus_id=campus_id,
        fecha__date__gte=date_from,
        fecha__date__lte=date_to,
    ).select_related('user', 'vehicle', 'tipo_falta', 'sanction').order_by('fecha')


def _headers():
    return [
        'fecha', 'codigo_usuario', 'nombre_usuario', 'placa',
        'codigo_falta', 'nivel', 'descripcion', 'estado', 'sancion_aplicada',
    ]


def _rows(records):
    rows = []
    for v in records:
        sancion = ''
        try:
            if v.sanction:
                sancion = v.sanction.tipo
        except Exception:
            pass
        rows.append([
            v.fecha.strftime('%Y-%m-%d %H:%M'),
            v.user.codigo_institucional,
            f'{v.user.nombre} {v.user.apellido}',
            v.vehicle.placa if v.vehicle else '',
            v.tipo_falta.codigo,
            v.tipo_falta.nivel,
            v.descripcion,
            v.estado,
            sancion,
        ])
    return rows


def generate_violations_report(campus_id: int, date_from: date, date_to: date, fmt: str) -> HttpResponse:
    from apps.reports.generators.occupancy import _to_xlsx, _to_pdf
    records = _queryset(campus_id, date_from, date_to)
    headers = _headers()
    rows = _rows(records)
    filename = f'infracciones_{date_from}_{date_to}'
    if fmt == 'xlsx':
        return _to_xlsx(headers, rows, filename)
    return _to_pdf(headers, rows, f'Reporte de Infracciones — {date_from} a {date_to}', filename)
