"""Tests críticos del dominio CertifAI · happy paths + edge cases.

Cubre los 3 flujos que NO PUEDEN FALLAR en producción:
  1. Verificación pública de certificado por hash
  2. Inscripción de participante a evento
  3. Generación de lote de certificados desde sesión
  4. Auth de cuenta pública (registro + login)

Cada test es independiente (--reuse-db está OK porque no compartimos state).
"""
from datetime import date, timedelta
import uuid

import pytest

from core.models import Certificado, ConfirmacionAsistencia, Participante
from tests.factories import (
    LoteFactory, ParticipanteFactory, SesionFactory, CertificadoFactory,
)


# ════════════════════════════════════════════════════════════════
#  1 · Verificación pública por hash (3 tests)
# ════════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_verify_certificate_happy_path(api_client):
    """Hash válido devuelve 200 con datos del certificado."""
    cert = CertificadoFactory(curso='Curso de Prueba', horas=40)
    res = api_client.get(f'/api/v1/public/verify/{cert.hash_verificacion}/')
    assert res.status_code == 200
    data = res.json()
    assert data['found'] is True
    assert data['certificado']['nombres'] == cert.nombres
    assert data['certificado']['curso'] == 'Curso de Prueba'


@pytest.mark.django_db
def test_verify_certificate_invalid_hash_returns_404(api_client):
    """Hash inexistente devuelve 404 — no filtra que el hash existe o no."""
    fake_hash = uuid.uuid4()
    res = api_client.get(f'/api/v1/public/verify/{fake_hash}/')
    assert res.status_code == 404


@pytest.mark.django_db
def test_verify_certificate_increments_search_counter(api_client):
    """Cada verify incrementa veces_buscado para analítica."""
    cert = CertificadoFactory()
    initial = cert.veces_buscado
    api_client.get(f'/api/v1/public/verify/{cert.hash_verificacion}/')
    cert.refresh_from_db()
    assert cert.veces_buscado == initial + 1


# ════════════════════════════════════════════════════════════════
#  2 · Inscripción a evento (cuenta de participante)  (3 tests)
# ════════════════════════════════════════════════════════════════

@pytest.fixture
def participante_logged_in(db, client):
    """Crea participante con cuenta y lo deja logueado vía sesión Django."""
    p = ParticipanteFactory(email='estudiante@unemi.edu.ec')
    p.set_password('test1234')
    p.save()
    session = client.session
    session['participante_id'] = p.id
    session.save()
    return p


@pytest.mark.django_db
def test_inscripcion_evento_creates_confirmacion(client, participante_logged_in, settings):
    """POST a /cuenta/eventos/<id>/inscribir/ crea ConfirmacionAsistencia."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    s = SesionFactory(activa=True, fecha=date.today() + timedelta(days=7))
    res = client.post(f'/cuenta/eventos/{s.id}/inscribir/', follow=False)
    assert res.status_code in (302, 200)
    assert ConfirmacionAsistencia.objects.filter(
        participante=participante_logged_in, sesion=s
    ).exists()


@pytest.mark.django_db
def test_inscripcion_evento_idempotent(client, participante_logged_in, settings):
    """Inscribirse 2 veces no crea duplicado (get_or_create)."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    s = SesionFactory(activa=True, fecha=date.today() + timedelta(days=7))
    client.post(f'/cuenta/eventos/{s.id}/inscribir/')
    client.post(f'/cuenta/eventos/{s.id}/inscribir/')
    count = ConfirmacionAsistencia.objects.filter(
        participante=participante_logged_in, sesion=s
    ).count()
    assert count == 1


@pytest.mark.django_db
def test_inscripcion_evento_inactiva_returns_404(client, participante_logged_in):
    """No se puede inscribir a una sesión activa=False."""
    s = SesionFactory(activa=False)
    res = client.post(f'/cuenta/eventos/{s.id}/inscribir/')
    assert res.status_code == 404
    assert not ConfirmacionAsistencia.objects.filter(participante=participante_logged_in).exists()


# ════════════════════════════════════════════════════════════════
#  3 · Generación de lote desde sesión (3 tests)
# ════════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_generate_batch_creates_certificates_and_links_lote(super_admin_client, settings):
    """Happy path: 3 confirmados → lote con 3 certs + sesion.lote enlazado."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    s = SesionFactory(activa=True, fecha=date.today(), lote=None)
    for i in range(3):
        p = ParticipanteFactory(email=f'p{i}@test.com', cedula='')
        ConfirmacionAsistencia.objects.create(participante=p, sesion=s, confirmado=True)

    res = super_admin_client.post(
        f'/api/v1/admin/sessions/{s.id}/generate-batch/',
        {'facultad': 'FACI'}, format='json',
    )
    assert res.status_code == 200, res.content
    data = res.json()
    assert data['certificados_creados'] == 3

    s.refresh_from_db()
    assert s.lote_id is not None
    assert Certificado.objects.filter(lote=s.lote).count() == 3
    # Cada cert tiene hash único
    hashes = list(Certificado.objects.filter(lote=s.lote).values_list('hash_verificacion', flat=True))
    assert len(set(hashes)) == 3


@pytest.mark.django_db
def test_generate_batch_409_if_already_has_lote(super_admin_client):
    """Si la sesión ya tiene lote, devuelve 409 — no crea uno nuevo."""
    s = SesionFactory(activa=True, lote=LoteFactory())
    res = super_admin_client.post(
        f'/api/v1/admin/sessions/{s.id}/generate-batch/',
        {'facultad': 'FACI'}, format='json',
    )
    assert res.status_code == 409


@pytest.mark.django_db
def test_generate_batch_404_if_no_confirmados(super_admin_client):
    """Sin participantes confirmados, devuelve 404 con mensaje claro."""
    s = SesionFactory(activa=True, lote=None)
    s.refresh_from_db()
    res = super_admin_client.post(
        f'/api/v1/admin/sessions/{s.id}/generate-batch/',
        {'facultad': 'FACI'}, format='json',
    )
    assert res.status_code == 404
    assert 'confirmados' in res.json().get('error', '').lower()


# ════════════════════════════════════════════════════════════════
#  4 · Auth de cuenta pública (3 tests)
# ════════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_register_creates_participante_with_password_hash(client, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    res = client.post('/cuenta/register/', {
        'nombres': 'Juan', 'apellidos': 'Pérez',
        'email': 'juan@unemi.edu.ec',
        'cedula': '', 'celular': '',  # opcionales
        'password': 'secret123', 'password2': 'secret123',
    })
    assert res.status_code == 302  # redirect a dashboard tras login
    p = Participante.objects.get(email='juan@unemi.edu.ec')
    assert p.has_account
    assert p.password_hash != ''
    assert p.check_password('secret123')


@pytest.mark.django_db
def test_register_rejects_password_mismatch(client):
    """Si password != password2, no crea cuenta."""
    res = client.post('/cuenta/register/', {
        'nombres': 'X', 'apellidos': 'Y', 'email': 'x@y.com',
        'password': 'aaaaaa', 'password2': 'bbbbbb',
    })
    # Re-render del form (200) — sin crear participante
    assert res.status_code == 200
    assert not Participante.objects.filter(email='x@y.com').exists()


@pytest.mark.django_db
def test_login_correct_credentials_creates_session(client):
    """Login válido pone participante_id en la sesión."""
    p = ParticipanteFactory(email='login@test.com')
    p.set_password('test1234')
    p.save()
    res = client.post('/cuenta/login/', {
        'email': 'login@test.com', 'password': 'test1234',
    })
    assert res.status_code == 302
    assert client.session.get('participante_id') == p.id


@pytest.mark.django_db
def test_login_wrong_password_keeps_no_session(client):
    """Password incorrecto no setea sesión."""
    p = ParticipanteFactory(email='wrong@test.com')
    p.set_password('test1234')
    p.save()
    res = client.post('/cuenta/login/', {
        'email': 'wrong@test.com', 'password': 'WRONG',
    })
    assert res.status_code == 200  # re-render del form
    assert client.session.get('participante_id') is None
