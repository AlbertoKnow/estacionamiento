from datetime import date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import Role
from apps.users.permissions import IsJefeSeguridad, IsJefeOperacionesOrAbove, IsDirectorOrAbove
from .generators.occupancy import generate_occupancy_report
from .generators.violations import generate_violations_report
from .generators.users import generate_users_report


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _resolve_campus_id(request):
    """
    Rector may request any campus via ?campus_id=.
    All other roles are locked to their own campus regardless of the query param.
    """
    user = request.user
    if user.rol == Role.RECTOR:
        campus_id = request.query_params.get('campus_id') or getattr(
            user.campus_asignado, 'id', None
        )
        return int(campus_id) if campus_id else None
    return getattr(user.campus_asignado, 'id', None)


class OccupancyReportView(APIView):
    permission_classes = [IsJefeSeguridad | IsJefeOperacionesOrAbove]

    def get(self, request):
        campus_id = _resolve_campus_id(request)
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to = _parse_date(request.query_params.get('date_to'))
        fmt = request.query_params.get('format', 'xlsx')

        if not campus_id or not date_from or not date_to:
            return Response(
                {'detail': 'Parámetros requeridos: campus_id, date_from, date_to.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return generate_occupancy_report(campus_id, date_from, date_to, fmt)


class ViolationsReportView(APIView):
    permission_classes = [IsJefeSeguridad | IsJefeOperacionesOrAbove]

    def get(self, request):
        campus_id = _resolve_campus_id(request)
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to = _parse_date(request.query_params.get('date_to'))
        fmt = request.query_params.get('format', 'xlsx')

        if not campus_id or not date_from or not date_to:
            return Response(
                {'detail': 'Parámetros requeridos: campus_id, date_from, date_to.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return generate_violations_report(campus_id, date_from, date_to, fmt)


class UsersReportView(APIView):
    permission_classes = [IsDirectorOrAbove]

    def get(self, request):
        campus_id = _resolve_campus_id(request)
        fmt = request.query_params.get('format', 'xlsx')

        if not campus_id:
            return Response(
                {'detail': 'El usuario no tiene campus asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return generate_users_report(campus_id, fmt)
