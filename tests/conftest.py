"""Fixtures compartidos para todos los tests."""
import pytest
from rest_framework.test import APIClient

from tests.factories import (
    UsuarioFactory, SuperAdminFactory,
    LoteFactory, ParticipanteFactory, SesionFactory, CertificadoFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return UsuarioFactory()


@pytest.fixture
def super_admin_user(db):
    return SuperAdminFactory()


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def super_admin_client(api_client, super_admin_user):
    api_client.force_authenticate(user=super_admin_user)
    return api_client


@pytest.fixture
def lote(db):
    return LoteFactory()


@pytest.fixture
def participante(db):
    return ParticipanteFactory()


@pytest.fixture
def sesion(db, lote):
    return SesionFactory(lote=lote)


@pytest.fixture
def certificado(db, lote, participante):
    return CertificadoFactory(lote=lote, participante=participante)
