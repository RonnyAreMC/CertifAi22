"""Enums (TextChoices) del sistema — catálogos estáticos definidos en código.

A diferencia de los modelos catálogo dinámicos (que viven en otros archivos
de este paquete), estos valores son fijos y se consultan por nombre en el
código. Cambiarlos requiere un cambio de código + migración.

Usar enums para:
- Estados de máquina de procesamiento (FSM)
- Roles de seguridad
- Tipos cerrados que NO se amplían sin cambiar lógica

Para entidades que el admin puede ampliar (facultades, plantillas, etc.)
preferir modelos catálogo dinámicos.
"""
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
