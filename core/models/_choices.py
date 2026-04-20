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


class LandingTipo(models.TextChoices):
    HERO = 'hero', 'Encabezado Principal'
    STATS = 'stats', 'Barra de Estadísticas'
    STEPS = 'steps', 'Pasos / Proceso'
    FEATURES = 'features', 'Características / Cards'
    CTA = 'cta', 'Call to Action / Banner'
    EVENTO = 'evento', 'Evento Destacado'
    PASADO = 'pasado', 'Evento Pasado / Noticia'
    CUSTOM = 'custom', 'Bloque Personalizado'


class LandingEstilo(models.TextChoices):
    HERO_GRADIENT = 'hero_gradient', 'Hero - Gradiente con orbes animados'
    HERO_IMAGEN = 'hero_imagen', 'Hero - Imagen de fondo completa'
    HERO_SPLIT = 'hero_split', 'Hero - Mitad imagen / mitad texto'
    STATS_BAR = 'stats_bar', 'Stats - Barra de estadísticas'
    STEPS_3 = 'steps_3', 'Steps - 3 pasos con iconos'
    FEATURES_GRID = 'features_grid', 'Features - Grid de características'
    CTA_BANNER = 'cta_banner', 'CTA - Banner con botón'
    CARD_IMAGEN_TOP = 'card_imagen_top', 'Card - Imagen arriba, texto abajo'
    CARD_HORIZONTAL = 'card_horizontal', 'Card - Imagen lateral, texto al lado'
    CARD_SOLO_TEXTO = 'card_solo_texto', 'Card - Solo texto con color de fondo'
