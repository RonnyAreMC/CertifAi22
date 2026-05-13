"""Factories para tests (factory-boy)."""
from datetime import date, time, timedelta
import uuid

import factory
from factory.django import DjangoModelFactory

from core.models import (
    Usuario, LoteCertificados, Participante, Certificado, SesionAsistencia,
)


class UsuarioFactory(DjangoModelFactory):
    class Meta:
        model = Usuario

    username = factory.Sequence(lambda n: f'admin{n}')
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    first_name = 'Admin'
    last_name = 'User'
    is_staff = True
    is_superuser = False
    is_active = True
    activo = True
    rol = 'admin'

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or 'testpass123')
        if create:
            obj.save()


class SuperAdminFactory(UsuarioFactory):
    is_superuser = True
    rol = 'superadmin'


class LoteFactory(DjangoModelFactory):
    class Meta:
        model = LoteCertificados

    nombre_lote = factory.Sequence(lambda n: f'Lote Test {n}')
    facultad = 'FACI'
    plantilla = 'clasico'
    activo = True


class ParticipanteFactory(DjangoModelFactory):
    class Meta:
        model = Participante

    cedula = factory.Sequence(lambda n: f'09{n:08d}')
    nombres = 'Juan'
    apellidos = 'Pérez'
    email = factory.Sequence(lambda n: f'juan{n}@test.com')
    celular = '0999999999'
    es_lider = False


class SesionFactory(DjangoModelFactory):
    class Meta:
        model = SesionAsistencia

    lote = factory.SubFactory(LoteFactory)
    titulo = factory.Sequence(lambda n: f'Sesión Test {n}')
    descripcion = 'Descripción de prueba'
    fecha = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    hora_inicio = time(10, 0)
    hora_fin = time(12, 0)
    capacidad = 50
    modalidad = 'presencial'
    lugar = 'Auditorio Test'
    activa = True


class CertificadoFactory(DjangoModelFactory):
    class Meta:
        model = Certificado

    lote = factory.SubFactory(LoteFactory)
    participante = factory.SubFactory(ParticipanteFactory)
    cedula = factory.Sequence(lambda n: f'09{n:08d}')
    nombres = 'Juan'
    apellidos = 'Pérez'
    email = factory.Sequence(lambda n: f'juan{n}@test.com')
    curso = 'Curso de Prueba'
    fecha_curso = factory.LazyFunction(date.today)
    horas = 40
    hash_verificacion = factory.LazyFunction(lambda: str(uuid.uuid4()))
