"""Tests de auditoría automática via AuditedModelViewSet."""
import pytest


@pytest.mark.django_db
class TestAuditedCRUD:
    def test_create_logs_audit(self, admin_client, lote):
        from core.models import Auditoria
        res = admin_client.post('/api/v1/admin/sessions/', {
            'titulo': 'Test Audit',
            'descripcion': '',
            'modalidad': 'presencial',
            'lugar': 'Test',
            'fecha': '2030-01-15',
            'hora_inicio': '10:00',
            'hora_fin': '12:00',
            'capacidad': 50,
            'lote': lote.id,
        }, format='json')
        assert res.status_code == 201, res.data
        assert Auditoria.objects.filter(accion='CREAR_SESION').count() == 1

    def test_delete_logs_audit(self, admin_client, sesion):
        from core.models import Auditoria
        admin_client.delete(f'/api/v1/admin/sessions/{sesion.id}/')
        assert Auditoria.objects.filter(accion='ELIMINAR_SESION').count() == 1

    def test_audit_endpoint_returns_entries(self, admin_client, sesion):
        admin_client.post(f'/api/v1/admin/sessions/{sesion.id}/toggle/')
        res = admin_client.get('/api/v1/admin/audit/')
        assert res.status_code == 200
        assert res.data['count'] >= 1
