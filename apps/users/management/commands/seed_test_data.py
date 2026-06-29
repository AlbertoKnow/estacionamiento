"""
Crea usuarios de prueba para todos los roles del sistema.

Uso:
    docker compose exec web python manage.py seed_test_data
    docker compose exec web python manage.py seed_test_data --reset

Credenciales generadas (codigo / contraseña):
    alumno01   / test1234   (alumno con auto + moto)
    docente01  / test1234   (académico con auto)
    agente01   / test1234   (agente de seguridad — escanea QR)
    asistente01/ test1234   (asistente operaciones — pone infracciones)
    jefe_op01  / test1234   (jefe de operaciones)
    jefe_seg01 / test1234   (jefe de seguridad)
    director01 / test1234   (director)
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import User, Vehicle, Role, VehicleType
from apps.spaces.models import Campus
from apps.violations.models import ViolationType, ViolationLevel


CAMPUS_NOMBRE = "UTP Arequipa"

USUARIOS = [
    {
        "codigo": "alumno01",
        "nombre": "Luis",
        "apellido": "Torres Quispe",
        "email": "alumno01@utp.edu.pe",
        "rol": Role.ALUMNO,
        "vehiculos": [
            ("VBO-159", VehicleType.AUTO),
            ("M-2341", VehicleType.MOTO),
        ],
    },
    {
        "codigo": "alumno02",
        "nombre": "María",
        "apellido": "Cahuana Flores",
        "email": "alumno02@utp.edu.pe",
        "rol": Role.ALUMNO,
        "vehiculos": [
            ("VDM-202", VehicleType.AUTO),
        ],
    },
    {
        "codigo": "docente01",
        "nombre": "Carlos",
        "apellido": "Mendoza Rivas",
        "email": "docente01@utp.edu.pe",
        "rol": Role.ACADEMICO,
        "vehiculos": [
            ("AQP-991", VehicleType.AUTO),
        ],
    },
    {
        "codigo": "agente01",
        "nombre": "Pedro",
        "apellido": "Mamani Ccallo",
        "email": "agente01@utp.edu.pe",
        "rol": Role.AGENTE_SEGURIDAD,
        "vehiculos": [],
    },
    {
        "codigo": "asistente01",
        "nombre": "Ana",
        "apellido": "Huanca Larico",
        "email": "asistente01@utp.edu.pe",
        "rol": Role.ASISTENTE_OPERACIONES,
        "vehiculos": [],
    },
    {
        "codigo": "jefe_op01",
        "nombre": "Roberto",
        "apellido": "Cáceres Pinto",
        "email": "jefe_op01@utp.edu.pe",
        "rol": Role.JEFE_OPERACIONES,
        "vehiculos": [],
    },
    {
        "codigo": "jefe_seg01",
        "nombre": "Sandra",
        "apellido": "Vera Molina",
        "email": "jefe_seg01@utp.edu.pe",
        "rol": Role.JEFE_SEGURIDAD,
        "vehiculos": [],
    },
    {
        "codigo": "director01",
        "nombre": "Miguel",
        "apellido": "Salinas Espinoza",
        "email": "director01@utp.edu.pe",
        "rol": Role.DIRECTOR,
        "vehiculos": [],
    },
]

TIPOS_FALTA = [
    # Faltas Leves — SEG-PT002 pág. 6-7
    ("L-A", "No acatar las recomendaciones e indicaciones del personal de Seguridad.", ViolationLevel.LEVE),
    ("L-B", "No respetar el uso del estacionamiento en el turno solicitado y sede asignada.", ViolationLevel.LEVE),
    ("L-C", "No permitir la revisión del vehículo por parte del personal de Seguridad, cada vez que se le solicite.", ViolationLevel.LEVE),
    ("L-D", "Tocar la bocina sin motivo urgente alguno.", ViolationLevel.LEVE),
    ("L-E", "Estacionarse incorrectamente, no respetar las demarcaciones y/o invadir otro estacionamiento.", ViolationLevel.LEVE),
    ("L-F", "No respetar los lugares asignados o reservados para la Directiva, Decanato, Gerencia u otros similares, que se encuentren identificados.", ViolationLevel.LEVE),
    ("L-G", "Mantener algún ocupante dentro del vehículo una vez estacionado.", ViolationLevel.LEVE),
    ("L-H", "No conducir con las luces del vehículo encendidas dentro del estacionamiento o no hacer uso de las luces direccionales correspondientes.", ViolationLevel.LEVE),
    ("L-I", "Permanecer frente a la puerta de ingreso o en la pista, esperando que se desocupe un espacio para ingresar; o impedir el libre tránsito.", ViolationLevel.LEVE),
    ("L-J", "No respetar las señales de tránsito dentro del estacionamiento.", ViolationLevel.LEVE),
    ("L-K", "Estacionar una motocicleta o bicicleta en una ubicación que no está destinada para ella.", ViolationLevel.LEVE),
    # Faltas Graves — SEG-PT002 pág. 7
    ("G-A", "No respetar las zonas rígidas y destinadas para las personas discapacitadas.", ViolationLevel.GRAVE),
    ("G-B", "No estacionar en las ubicaciones destinadas según su tipo de vehículo.", ViolationLevel.GRAVE),
    ("G-C", "Exceder la velocidad de 10 km/h dentro del estacionamiento.", ViolationLevel.GRAVE),
    ("G-D", "Realizar maniobras temerarias dentro del estacionamiento.", ViolationLevel.GRAVE),
    ("G-E", "Dejar el vehículo pernoctando en el estacionamiento sin haber seguido el procedimiento de información/autorización establecidos.", ViolationLevel.GRAVE),
    ("G-F", "No respetar al personal de Seguridad (agredir física o verbalmente) o a cualquier colaborador de la institución.", ViolationLevel.GRAVE),
    # Faltas Muy Graves — SEG-PT002 pág. 7
    ("MG-G", "Usar o permitir el uso del Fotocheck por parte de cualquier persona distinta al colaborador (docente o administrativo) titular de la autorización.", ViolationLevel.MUY_GRAVE),
    ("MG-H", "Realizar modificaciones y/o adulteraciones al Fotocheck usando mecanismos digitales.", ViolationLevel.MUY_GRAVE),
]


class Command(BaseCommand):
    help = "Crea usuarios de prueba para todos los roles del sistema"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Eliminar usuarios de prueba existentes antes de crear",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            codigos = [u["codigo"] for u in USUARIOS]
            deleted, _ = User.objects.filter(codigo_institucional__in=codigos).delete()
            self.stdout.write(self.style.WARNING(f"  Eliminados {deleted} usuarios de prueba"))

        campus = Campus.objects.filter(nombre=CAMPUS_NOMBRE).first()
        if not campus:
            self.stdout.write(
                self.style.ERROR(
                    f"Campus '{CAMPUS_NOMBRE}' no encontrado. "
                    "Ejecuta primero: docker compose exec web python scripts/import_data.py"
                )
            )
            return

        self.stdout.write("\n=== Tipos de falta ===")
        with transaction.atomic():
            for codigo, desc, nivel in TIPOS_FALTA:
                _, created = ViolationType.objects.get_or_create(
                    codigo=codigo,
                    defaults={"descripcion": desc, "nivel": nivel},
                )
                status = "creado" if created else "ya existe"
                self.stdout.write(f"  [{nivel.upper():9}] {codigo} — {status}")

        self.stdout.write("\n=== Usuarios de prueba ===")
        with transaction.atomic():
            for data in USUARIOS:
                user, created = User.objects.get_or_create(
                    codigo_institucional=data["codigo"],
                    defaults={
                        "nombre": data["nombre"],
                        "apellido": data["apellido"],
                        "email": data["email"],
                        "rol": data["rol"],
                        "campus_asignado": campus,
                    },
                )
                if created:
                    user.set_password("test1234")
                    user.save()

                status = "creado" if created else "ya existe"
                self.stdout.write(
                    f"  [{data['rol']:25}] {data['codigo']:15} — {status}"
                )

                for placa, tipo in data["vehiculos"]:
                    _, vc = Vehicle.objects.get_or_create(
                        placa=placa,
                        defaults={"user": user, "tipo": tipo, "activo": True},
                    )
                    vstatus = "creado" if vc else "ya existe"
                    self.stdout.write(f"    Vehículo {placa} ({tipo}) — {vstatus}")

        self.stdout.write(self.style.SUCCESS("\n=== Listo ==="))
        self.stdout.write(
            "\nCredenciales (codigo / contraseña):\n"
            "  alumno01    / test1234   → rol: alumno (auto VBO-159, moto M-2341)\n"
            "  alumno02    / test1234   → rol: alumno (auto VDM-202)\n"
            "  docente01   / test1234   → rol: académico (auto AQP-991)\n"
            "  agente01    / test1234   → rol: agente de seguridad (escanea QR)\n"
            "  asistente01 / test1234   → rol: asistente de operaciones (pone infracciones)\n"
            "  jefe_op01   / test1234   → rol: jefe de operaciones\n"
            "  jefe_seg01  / test1234   → rol: jefe de seguridad\n"
            "  director01  / test1234   → rol: director\n"
            "  admin       / admin123   → rol: rector (superusuario)\n"
        )
