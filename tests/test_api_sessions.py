"""Tests de API de sesiones (CRUD + custom actions + auditoría)."""
import pytest

from tests.factories import SesionFactory


@pytest.mark.django_db
class TestSesionAPI:
    def test_list_requires_admin(self, api_client):
        res = api_client.get('/api/v1/admin/sessions/')
        assert res.status_code == 401

    def test_admin_can_list(self, admin_client):
        SesionFactory()
        SesionFactory()
        res = admin_client.get('/api/v1/admin/sessions/')
        assert res.status_code == 200
        assert res.data['count'] == 2

    def test_toggle_flips_activa(self, admin_client, sesion):
        assert sesion.activa is True
        res = admin_client.post(f'/api/v1/admin/sessions/{sesion.id}/toggle/')
        assert res.status_code == 200
        assert res.data['activa'] is False
        sesion.refresh_from_db()
        assert sesion.activa is False

    def test_toggle_creates_audit_entry(self, admin_client, sesion):
        from core.models import Auditoria
        before = Auditoria.objects.filter(accion='TOGGLE_SESION').count()
        admin_client.post(f'/api/v1/admin/sessions/{sesion.id}/toggle/')
        after = Auditoria.objects.filter(accion='TOGGLE_SESION').count()
        assert after == before + 1

    def test_delete_rejects_with_confirmaciones(self, admin_client, sesion, participante):
        from core.models import ConfirmacionAsistencia
        ConfirmacionAsistencia.objects.create(
            sesion=sesion, participante=participante, confirmado=True,
        )
        res = admin_client.delete(f'/api/v1/admin/sessions/{sesion.id}/')
        assert res.status_code == 409
        assert 'error' in res.data


@pytest.mark.django_db
class TestPublicSesionAPI:
    def test_upcoming_is_public(self, api_client):
        SesionFactory()
        res = api_client.get('/api/v1/public/sessions/upcoming/')
        assert res.status_code == 200
