from rest_framework.permissions import BasePermission
from .models import Role

ROLE_HIERARCHY = [
    Role.RECTOR,
    Role.DIRECTOR,
    Role.JEFE_OPERACIONES,
    Role.JEFE_SEGURIDAD,
    Role.ASISTENTE_OPERACIONES,
    Role.AGENTE_SEGURIDAD,
    Role.ADMINISTRATIVO,
    Role.ACADEMICO,
    Role.ALUMNO,
]


def _has_role_or_above(user, min_role: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    try:
        user_index = ROLE_HIERARCHY.index(user.rol)
        min_index = ROLE_HIERARCHY.index(min_role)
        return user_index <= min_index
    except ValueError:
        return False


class IsRector(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.RECTOR)


class IsDirectorOrAbove(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.DIRECTOR)


class IsJefeOperacionesOrAbove(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.JEFE_OPERACIONES)


class IsJefeSeguridad(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.JEFE_SEGURIDAD)


class IsOperativoOrAbove(BasePermission):
    """Agente de Seguridad, Asistente de Operaciones y superiores."""
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.AGENTE_SEGURIDAD)


class IsUsuarioFinal(BasePermission):
    """Administrativo, Académico, Alumno."""
    FINAL_ROLES = {Role.ADMINISTRATIVO, Role.ACADEMICO, Role.ALUMNO}

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in self.FINAL_ROLES
        )


class IsSameCampusOrAbove(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.rol == Role.RECTOR:
            return True
        obj_campus = getattr(obj, 'campus_asignado', None) or getattr(obj, 'campus', None)
        return obj_campus == request.user.campus_asignado
