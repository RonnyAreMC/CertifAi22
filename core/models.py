from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError

FACULTADES_CHOICES = [
    ('FACI', 'FACI - Ingeniería'),
    ('FACS', 'FACS - Salud'),
    ('FACE', 'FACE - Educación'),
    ('FACSECYD', 'FACSECYD - Ciencias Sociales'),
    ('POSGRADO', 'Posgrado / Otra'),
]

class Usuario(AbstractUser):
    """Usuario del sistema (solo administradores)"""
    ROLES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='admin')
    facultad = models.CharField(
        max_length=20, 
        choices=FACULTADES_CHOICES, 
        blank=True
    )
    telefono = models.CharField(max_length=20, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"

class FirmaInstitucional(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre Autoridad", blank=True)
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    imagen = models.TextField(verbose_name="Firma (Base64)", blank=True, default='')
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden por defecto")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Firma Institucional'
        verbose_name_plural = 'Firmas Institucionales'
        
    def __str__(self):
        return f"{self.nombre} ({self.cargo})"

class DisenoGlobal(models.Model):
    """
    Configuración de diseño GLOBAL para todos los certificados.
    Es un singleton: siempre existe una sola fila (id=1).
    Solo el superadmin puede modificarlo.
    """
    PLANTILLAS = [
        ('clasico', 'Clásico (Elegante)'),
        ('moderno', 'Moderno (Barra Lateral)'),
        ('geometrico', 'Geométrico (Formas)'),
    ]
    plantilla = models.CharField(max_length=20, choices=PLANTILLAS, default='clasico')
    color_primario = models.CharField(max_length=7, default='#162054')
    color_secundario = models.CharField(max_length=7, default='#D4AF37')
    color_terciario = models.CharField(max_length=7, default='#F3F4F6')
    color_texto = models.CharField(max_length=7, default='#333333')

    cuerpo_certificado = models.TextField(
        default="Por haber completado satisfactoriamente el curso de capacitación continua, demostrando compromiso y excelencia académica. Por su participación en el seminario '{curso}', contribuyendo de manera activa y profesional al desarrollo de nuevas competencias.",
    )

    firma_inst_1 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='diseno_firma1')
    firma_inst_2 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='diseno_firma2')
    firma_inst_3 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='diseno_firma3')

    # Firma personalizada (opcional)
    nombre_firma_4 = models.CharField(max_length=100, blank=True, default='')
    cargo_firma_4 = models.CharField(max_length=100, blank=True, default='')
    imagen_firma_4 = models.TextField(blank=True, default='')

    logo_header_1 = models.ImageField(upload_to='logos/', null=True, blank=True)
    logo_header_2 = models.ImageField(upload_to='logos/', null=True, blank=True)
    logo_header_3 = models.ImageField(upload_to='logos/', null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diseño Global'
        verbose_name_plural = 'Diseño Global'

    def __str__(self):
        return f"Diseño Global ({self.get_plantilla_display()})"

    def save(self, *args, **kwargs):
        # Garantizar singleton
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class LoteCertificados(models.Model):
    nombre_lote = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    archivo_excel = models.FileField(upload_to='lotes_excel/', null=True, blank=True)
    administrador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    activo = models.BooleanField(default=True)
    
    facultad = models.CharField(max_length=20, choices=FACULTADES_CHOICES, default='FACI', db_index=True)

    # Si está en False (default) el lote usa el Diseño Global.
    # Si el admin lo activa, el lote usa sus propios valores de los campos siguientes.
    personalizar_diseno = models.BooleanField(
        default=False,
        verbose_name='Personalizar diseño para este lote',
        help_text='Si está activo, este lote usará su propio diseño en lugar del Diseño Global.'
    )

    # Customization Fields
    PLANTILLAS = [
        ('clasico', 'Clásico (Elegante)'),
        ('moderno', 'Moderno (Barra Lateral)'),
        ('geometrico', 'Geométrico (Formas)'),
    ]
    plantilla = models.CharField(max_length=20, choices=PLANTILLAS, default='clasico')
    color_primario = models.CharField(max_length=7, default='#162054', help_text="Color Principal (Hex)")
    color_secundario = models.CharField(max_length=7, default='#D4AF37', help_text="Color Secundario (Hex)")
    color_terciario = models.CharField(max_length=7, default='#F3F4F6', help_text="Color Terciario/Detalle (Hex)")
    color_texto = models.CharField(max_length=7, default='#333333', help_text="Color del Texto (Hex)")

    cuerpo_certificado = models.TextField(
        default="Por haber completado satisfactoriamente el curso de capacitación continua, demostrando compromiso y excelencia académica. Por su participación en el seminario '{curso}', contribuyendo de manera activa y profesional al desarrollo de nuevas competencias.",
        help_text="Texto principal del certificado"
    )
    
    # Firma 1 (Principal - e.g., Rector)
    firma_inst_1 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma1', verbose_name="Firma Institucional 1")
    nombre_firma_1 = models.CharField(max_length=100, blank=True, default="", verbose_name="Nombre Autoridad 1")
    cargo_firma_1 = models.CharField(max_length=100, blank=True, default="", verbose_name="Cargo Autoridad 1")
    imagen_firma_1 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 1 (Base64)")

    # Firma 2 (Secundaria - e.g., Decano/Vicerrectora)
    firma_inst_2 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma2', verbose_name="Firma Institucional 2")
    nombre_firma_2 = models.CharField(max_length=100, blank=True, default="", verbose_name="Nombre Autoridad 2")
    cargo_firma_2 = models.CharField(max_length=100, blank=True, default="", verbose_name="Cargo Autoridad 2")
    imagen_firma_2 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 2 (Base64)")

    # Firma 3 (Opcional)
    firma_inst_3 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma3', verbose_name="Firma Institucional 3")
    nombre_firma_3 = models.CharField(max_length=100, blank=True, verbose_name="Nombre Autoridad 3")
    cargo_firma_3 = models.CharField(max_length=100, blank=True, verbose_name="Cargo Autoridad 3")
    imagen_firma_3 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 3 (Base64)")

    # Firma 4 (Opcional)
    firma_inst_4 = models.ForeignKey(FirmaInstitucional, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma4', verbose_name="Firma Institucional 4")
    nombre_firma_4 = models.CharField(max_length=100, blank=True, verbose_name="Nombre Autoridad 4")
    cargo_firma_4 = models.CharField(max_length=100, blank=True, verbose_name="Cargo Autoridad 4")
    imagen_firma_4 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 4 (Base64)")

    # Header Logos (Opcional, hasta 3)
    logo_header_1 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 1")
    logo_header_2 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 2")
    logo_header_3 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 3")

    def __str__(self):
        return self.nombre_lote

class Participante(models.Model):
    """Registro único de un participante/estudiante en el sistema."""
    cedula = models.CharField(max_length=20, blank=True, default='', db_index=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=200, db_index=True)
    celular = models.CharField(max_length=20, blank=True, default='')
    es_lider = models.BooleanField(default=False, verbose_name='Líder Académico', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'
        constraints = [
            models.UniqueConstraint(
                fields=['cedula'],
                name='unique_cedula_when_not_empty',
                condition=~models.Q(cedula=''),
            ),
        ]
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cedula']),
        ]

    def clean(self):
        if not self.cedula and not self.email:
            raise ValidationError('Debe proporcionar al menos cédula o correo electrónico.')

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula or self.email})"


class Certificado(models.Model):
    lote = models.ForeignKey(LoteCertificados, on_delete=models.CASCADE, related_name='certificados')
    participante = models.ForeignKey(
        'Participante', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='certificados'
    )
    cedula = models.CharField(max_length=20, db_index=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=200, db_index=True)
    celular = models.CharField(max_length=20, null=True, blank=True)
    
    # Metadata del curso/evento
    curso = models.CharField(max_length=255)
    fecha_curso = models.DateField(null=True, blank=True)
    horas = models.IntegerField(default=0)
    
    # Seguridad y Acceso
    hash_verificacion = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    pdf_generado = models.FileField(upload_to='certificados_pdf/', null=True, blank=True)
    
    # Metricas
    descargas_count = models.IntegerField(default=0)
    veces_buscado = models.IntegerField(default=0)
    fecha_ultima_descarga = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cedula} - {self.curso}"

class Auditoria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    accion = models.CharField(max_length=50)  # CREAR, ELIMINAR, EDITAR
    detalle = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        
    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.fecha}"


class SesionAsistencia(models.Model):
    """Una sesión de un día/horario específico para tomar asistencia."""
    DIAS_SEMANA = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]

    lote = models.ForeignKey(
        LoteCertificados, on_delete=models.CASCADE,
        related_name='sesiones', verbose_name='Seminario',
        null=True, blank=True
    )
    titulo = models.CharField(
        max_length=200, blank=True,
        help_text='Título descriptivo (ej: "Sesión Mañana - Lunes")'
    )
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')
    lugar = models.CharField(max_length=300, blank=True, default='', verbose_name='Lugar')
    fecha = models.DateField(verbose_name='Fecha de la Sesión')
    dia_semana = models.CharField(
        max_length=12, choices=DIAS_SEMANA, verbose_name='Día'
    )
    hora_inicio = models.TimeField(verbose_name='Hora Inicio')
    hora_fin = models.TimeField(verbose_name='Hora Fin')
    codigo_qr = models.CharField(
        max_length=64, unique=True, default=uuid.uuid4,
        editable=False, db_index=True
    )
    capacidad = models.PositiveIntegerField(
        default=0, verbose_name='Cupos Máximos',
        help_text='0 = ilimitado'
    )
    solo_lideres = models.BooleanField(
        default=False, verbose_name='Solo Líderes Académicos',
        help_text='Solo participantes marcados como líderes pueden registrarse'
    )
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name = 'Sesión de Asistencia'
        verbose_name_plural = 'Sesiones de Asistencia'
        indexes = [
            models.Index(fields=['codigo_qr']),
            models.Index(fields=['fecha', 'activa']),
        ]

    def __str__(self):
        return (
            f"{self.dia_semana} {self.fecha} "
            f"({self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M})"
        )

    @property
    def label(self):
        return f"{self.hora_inicio:%H:%M} – {self.hora_fin:%H:%M}"

    @property
    def capacidad_ilimitada(self):
        return self.capacidad == 0

    @property
    def confirmados_count(self):
        return self.confirmaciones.count()

    @property
    def cupos_disponibles(self):
        if self.capacidad_ilimitada:
            return None  # None = ilimitado
        return max(0, self.capacidad - self.confirmados_count)

    @property
    def esta_llena(self):
        if self.capacidad_ilimitada:
            return False
        return self.confirmados_count >= self.capacidad


class RegistroAsistencia(models.Model):
    """Marca de asistencia al escanear el QR durante la sesión."""
    sesion = models.ForeignKey(
        SesionAsistencia, on_delete=models.CASCADE,
        related_name='registros'
    )
    certificado = models.ForeignKey(
        Certificado, on_delete=models.CASCADE,
        related_name='asistencias',
        null=True, blank=True
    )
    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE,
        related_name='asistencias',
        null=True, blank=True
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        unique_together = [('sesion', 'participante')]
        ordering = ['-fecha_registro']
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'

    def __str__(self):
        nombre = self.participante.nombres if self.participante else (self.certificado.nombres if self.certificado else '?')
        return f"{nombre} → {self.sesion}"


class ConfirmacionAsistencia(models.Model):
    """Confirmación previa: el participante se compromete a asistir."""
    certificado = models.ForeignKey(
        Certificado, on_delete=models.CASCADE,
        related_name='confirmaciones',
        null=True, blank=True
    )
    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE,
        related_name='confirmaciones',
        null=True, blank=True
    )
    sesion = models.ForeignKey(
        SesionAsistencia, on_delete=models.CASCADE,
        related_name='confirmaciones'
    )
    confirmado = models.BooleanField(default=True)
    bloqueado = models.BooleanField(
        default=False,
        help_text='Si faltó sin justificación, se bloquea la cuenta.'
    )
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('participante', 'sesion')]
        ordering = ['-fecha_confirmacion']
        verbose_name = 'Confirmación de Asistencia'
        verbose_name_plural = 'Confirmaciones de Asistencia'

    def __str__(self):
        nombre = self.participante.nombres if self.participante else (self.certificado.nombres if self.certificado else '?')
        status = 'Bloqueado' if self.bloqueado else 'Confirmado'
        return f"{nombre} — {status}"


class SolicitudAcceso(models.Model):
    """Solicitud de acceso para nuevos administradores - requiere aprobación"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Aprobación'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    email = models.EmailField(unique=True, verbose_name='Email')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    facultad = models.CharField(
        max_length=20, 
        choices=FACULTADES_CHOICES, 
        default='FACI',
        verbose_name='Facultad / Departamento'
    )
    
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente',
        db_index=True
    )
    
    usuario_creado = models.OneToOneField(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='solicitud_acceso',
        verbose_name='Usuario Creado'
    )
    
    # Auditoría
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    aprobado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='solicitudes_aprobadas',
        verbose_name='Aprobado por'
    )
    motivo_rechazo = models.TextField(blank=True, verbose_name='Motivo del Rechazo')
    
    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = 'Solicitud de Acceso'
        verbose_name_plural = 'Solicitudes de Acceso'
        indexes = [
            models.Index(fields=['estado', '-fecha_solicitud']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.get_estado_display()}"


class LandingBloque(models.Model):
    """Bloque configurable del landing page público."""
    TIPO_CHOICES = [
        ('hero', 'Encabezado Principal'),
        ('stats', 'Barra de Estadísticas'),
        ('steps', 'Pasos / Proceso'),
        ('features', 'Características / Cards'),
        ('cta', 'Call to Action / Banner'),
        ('evento', 'Evento Destacado'),
        ('pasado', 'Evento Pasado / Noticia'),
        ('custom', 'Bloque Personalizado'),
    ]
    ESTILO_CHOICES = [
        ('hero_gradient', 'Hero - Gradiente con orbes animados'),
        ('hero_imagen', 'Hero - Imagen de fondo completa'),
        ('hero_split', 'Hero - Mitad imagen / mitad texto'),
        ('stats_bar', 'Stats - Barra de estadísticas'),
        ('steps_3', 'Steps - 3 pasos con iconos'),
        ('features_grid', 'Features - Grid de características'),
        ('cta_banner', 'CTA - Banner con botón'),
        ('card_imagen_top', 'Card - Imagen arriba, texto abajo'),
        ('card_horizontal', 'Card - Imagen lateral, texto al lado'),
        ('card_solo_texto', 'Card - Solo texto con color de fondo'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='hero')
    estilo = models.CharField(max_length=30, choices=ESTILO_CHOICES, default='hero_gradient')
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    # Contenido
    titulo = models.CharField(max_length=200, blank=True)
    subtitulo = models.CharField(max_length=300, blank=True)
    descripcion = models.TextField(blank=True)

    # Items JSON (para stats, steps, features — lista de objetos)
    # Ej stats: [{"icono":"fa-solid fa-certificate","valor":"5,000+","label":"Certificados","color":"blue"}]
    # Ej steps: [{"icono":"fa-solid fa-search","titulo":"Busca","desc":"...","numero":"1"}]
    # Ej features: [{"icono":"fa-solid fa-shield","titulo":"Seguro","desc":"...","color":"blue"}]
    items_json = models.JSONField(default=list, blank=True)

    # Imágenes
    imagen_principal = models.ImageField(upload_to='landing/', null=True, blank=True)
    imagen_2 = models.ImageField(upload_to='landing/', null=True, blank=True)
    imagen_3 = models.ImageField(upload_to='landing/', null=True, blank=True)

    # Colores
    color_fondo = models.CharField(max_length=7, default='#162054')
    color_texto = models.CharField(max_length=7, default='#FFFFFF')
    color_acento = models.CharField(max_length=7, default='#F58830')

    # Evento vinculado
    sesion = models.ForeignKey(
        SesionAsistencia, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='landing_bloques',
        verbose_name='Evento vinculado'
    )

    # Botones configurables (hasta 2)
    boton_1_texto = models.CharField(max_length=100, blank=True)
    boton_1_url = models.CharField(max_length=500, blank=True)
    boton_1_icono = models.CharField(max_length=50, blank=True, default='fa-solid fa-arrow-right')
    boton_2_texto = models.CharField(max_length=100, blank=True)
    boton_2_url = models.CharField(max_length=500, blank=True)
    boton_2_icono = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden']
        verbose_name = 'Bloque de Landing'
        verbose_name_plural = 'Bloques de Landing'

    def __str__(self):
        return f"[{self.orden}] {self.get_tipo_display()} - {self.titulo or 'Sin título'}"
