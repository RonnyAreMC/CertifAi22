"""Constantes y choices compartidos entre módulos de models."""
from django.db import models


FACULTADES_CHOICES = [
    ('FACI', 'FACI - Ingeniería'),
    ('FACS', 'FACS - Salud'),
    ('FACE', 'FACE - Educación'),
    ('FACSECYD', 'FACSECYD - Ciencias Sociales'),
    ('POSGRADO', 'Posgrado / Otra'),
]


class Rol(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Super Administrador'
    ADMIN = 'admin', 'Administrador'


class EstadoSolicitud(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente de Aprobación'
    APROBADO = 'aprobado', 'Aprobado'
    RECHAZADO = 'rechazado', 'Rechazado'


class Plantilla(models.TextChoices):
    CLASICO = 'clasico', 'Clásico (Elegante)'
    MODERNO = 'moderno', 'Moderno (Barra Lateral)'
    GEOMETRICO = 'geometrico', 'Geométrico (Formas)'


class DiaSemana(models.TextChoices):
    LUNES = 'Lunes', 'Lunes'
    MARTES = 'Martes', 'Martes'
    MIERCOLES = 'Miércoles', 'Miércoles'
    JUEVES = 'Jueves', 'Jueves'
    VIERNES = 'Viernes', 'Viernes'
    SABADO = 'Sábado', 'Sábado'
    DOMINGO = 'Domingo', 'Domingo'


class Modalidad(models.TextChoices):
    PRESENCIAL = 'presencial', 'Presencial'
    VIRTUAL = 'virtual', 'Virtual'


class PlataformaVirtual(models.TextChoices):
    ZOOM = 'zoom', 'Zoom'
    MEET = 'meet', 'Google Meet'
    TEAMS = 'teams', 'Microsoft Teams'
    OTRO = 'otro', 'Otra plataforma'


