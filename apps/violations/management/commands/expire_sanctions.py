from django.core.management.base import BaseCommand
from apps.violations.sanctions import expire_sanctions


class Command(BaseCommand):
    help = 'Reactiva acceso de usuarios cuya suspensión temporal ha vencido'

    def handle(self, *args, **options):
        expire_sanctions()
        self.stdout.write(self.style.SUCCESS('Sanciones expiradas procesadas correctamente.'))
