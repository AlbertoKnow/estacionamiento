import io
import pytest
from datetime import timedelta
from django.http import HttpResponse
from django.utils import timezone
from apps.users.models import User, Role
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType, SpaceState


@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa', ciudad='Arequipa',
        direccion='Av. Parra 201', horario_operacion={},
    )


@pytest.fixture
def user_alumno(campus_arequipa):
    return User.objects.create_user(
        codigo_institucional='ALU001', email='alu001@utp.edu.pe',
        password='testpass123', nombre='Luis', apellido='Torres',
        rol=Role.ALUMNO, campus_asignado=campus_arequipa,
    )


@pytest.fixture
def access_record(campus_arequipa, user_alumno, db):
    from apps.access.models import AccessRecord, AccessState
    from apps.users.models import Vehicle
    lot = ParkingLot.objects.create(campus=campus_arequipa, nombre='Sótano 2', nivel=-2)
    space = ParkingSpace.objects.create(
        lot=lot, numero='A-01', tipo=SpaceType.AUTO, estado=SpaceState.LIBRE
    )
    vehicle = Vehicle.objects.create(
        user=user_alumno, placa='ABC-123', tipo='auto',
        marca='Toyota', modelo='Corolla', color='Blanco',
    )
    return AccessRecord.objects.create(
        user=user_alumno, vehicle=vehicle, campus=campus_arequipa, space=space,
        registrado_por=user_alumno,
        entrada_at=timezone.now() - timedelta(hours=2),
        salida_at=timezone.now() - timedelta(hours=1),
        estado=AccessState.COMPLETADO,
    )


@pytest.mark.django_db
class TestOccupancyReport:
    def test_xlsx_returns_valid_response(self, campus_arequipa, access_record):
        from apps.reports.generators.occupancy import generate_occupancy_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_occupancy_report(campus_arequipa.id, date_from, date_to, 'xlsx')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert len(response.content) > 0

    def test_pdf_returns_valid_response(self, campus_arequipa, access_record):
        from apps.reports.generators.occupancy import generate_occupancy_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_occupancy_report(campus_arequipa.id, date_from, date_to, 'pdf')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/pdf'
        assert len(response.content) > 0

    def test_xlsx_with_no_records(self, campus_arequipa):
        from apps.reports.generators.occupancy import generate_occupancy_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_occupancy_report(campus_arequipa.id, date_from, date_to, 'xlsx')
        assert isinstance(response, HttpResponse)
        assert len(response.content) > 0


@pytest.mark.django_db
class TestViolationsReport:
    def test_xlsx_returns_valid_response(self, campus_arequipa, user_alumno):
        from apps.reports.generators.violations import generate_violations_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_violations_report(campus_arequipa.id, date_from, date_to, 'xlsx')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def test_pdf_returns_valid_response(self, campus_arequipa, user_alumno):
        from apps.reports.generators.violations import generate_violations_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_violations_report(campus_arequipa.id, date_from, date_to, 'pdf')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/pdf'


@pytest.mark.django_db
class TestUsersReport:
    def test_xlsx_hcm_columns_present(self, campus_arequipa, user_alumno):
        import openpyxl
        from apps.reports.generators.users import generate_users_report
        response = generate_users_report(campus_arequipa.id, 'xlsx')
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        assert 'codigo_institucional' in headers
        assert 'nombre' in headers
        assert 'email' in headers
        assert 'rol' in headers
        assert 'estado' in headers

    def test_users_report_pdf(self, campus_arequipa, user_alumno):
        from apps.reports.generators.users import generate_users_report
        response = generate_users_report(campus_arequipa.id, 'pdf')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/pdf'

    def test_reservations_release_command(self, campus_arequipa, db):
        from django.core.management import call_command
        call_command('release_reservations')
