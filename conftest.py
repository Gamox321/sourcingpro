import pytest
from django.conf import settings
from django.utils import timezone


def pytest_configure():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


def _create_user(email, password, nombre, is_active=True):
    from apps.accounts.models import User
    user = User(email=email, nombre=nombre, is_active=is_active)
    user.set_password(password)
    user.save()
    return user


def _assign_role(user, role_name, descripcion=''):
    from apps.accounts.models import Role, UserRole
    role, _ = Role.objects.get_or_create(
        nombre=role_name,
        defaults={'descripcion': descripcion},
    )
    UserRole.objects.create(usuario=user, rol=role)
    return user


@pytest.fixture
def admin_user(db):
    user = _create_user('admin@test.cl', 'TestPass1!', 'Admin Test')
    _assign_role(user, 'administrador')
    return user


@pytest.fixture
def rrhh_user(db):
    user = _create_user('rrhh@test.cl', 'TestPass1!', 'RRHH Test')
    _assign_role(user, 'rrhh')
    return user


@pytest.fixture
def logistica_user(db):
    user = _create_user('logistica@test.cl', 'TestPass1!', 'Logistica Test')
    _assign_role(user, 'logistica')
    return user


@pytest.fixture
def jefatura_user(db):
    user = _create_user('jefe@test.cl', 'TestPass1!', 'Jefe Test')
    _assign_role(user, 'jefatura')
    return user


@pytest.fixture
def client_fixture(db):
    from apps.clients.models import Client
    return Client.objects.create(nombre='Test Client')


@pytest.fixture
def cost_center(db, client_fixture, jefatura_user):
    from apps.clients.models import CostCenter
    return CostCenter.objects.create(
        nombre='Test CeCo',
        codigo='TST-001',
        cliente=client_fixture,
        jefatura=jefatura_user,
    )


@pytest.fixture
def worker_fixture(db, cost_center):
    from apps.workers.models import Worker
    return Worker.objects.create(
        run='12345678-5',
        nombre='Trabajador Test',
        correo='trabajador@test.cl',
        cargo='Operario',
        estado=Worker.EstadoChoices.ACTIVO,
        centro_costo_actual=cost_center,
    )


@pytest.fixture
def epp_type(db):
    from apps.inventory.models import AssetType
    obj, _ = AssetType.objects.get_or_create(
        nombre='EPP',
        defaults={'estado': AssetType.EstadoChoices.ACTIVO},
    )
    return obj


@pytest.fixture
def epp_asset(db, epp_type):
    from apps.inventory.models import Asset
    return Asset.objects.create(
        codigo='EPP-001',
        nombre='Casco Seguridad',
        tipo=epp_type,
        estado=Asset.EstadoChoices.DISPONIBLE,
    )
