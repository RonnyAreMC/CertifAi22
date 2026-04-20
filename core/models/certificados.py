"""Modelos de lotes y certificados emitidos."""
import uuid
from django.db import models

from core.base.models import TimestampedModel
from core.managers import CertificadoManager, LoteManager

from ._choices import FACULTADES_CHOICES, Plantilla


class LoteCertificados(models.Model):
    """Lote de certificados generados para un curso/evento.

    Relación con DisenoGlobal:
      - Si `personalizar_diseno=False` (default) → el lote hereda del DisenoGlobal
        en tiempo de renderizado (ver `core.services.pdf._diseno._apply_diseno_global`).
      - Si `personalizar_diseno=True` → usa los campos propios (colors, firmas, etc.).
    """
    nombre_lote = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    archivo_excel = models.FileField(upload_to='lotes_excel/', null=True, blank=True)
    administrador = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True)
    activo = models.BooleanField(default=True)

    facultad = models.CharField(max_length=20, choices=FACULTADES_CHOICES, default='FACI', db_index=True)

    personalizar_diseno = models.BooleanField(
        default=False,
        verbose_name='Personalizar diseño para este lote',
        help_text='Si está activo, este lote usará su propio diseño en lugar del Diseño Global.'
    )

    plantilla = models.CharField(max_length=20, choices=Plantilla.choices, default=Plantilla.CLASICO)
    color_primario = models.CharField(max_length=7, default='#162054', help_text="Color Principal (Hex)")
    color_secundario = models.CharField(max_length=7, default='#D4AF37', help_text="Color Secundario (Hex)")
    color_terciario = models.CharField(max_length=7, default='#F3F4F6', help_text="Color Terciario/Detalle (Hex)")
    color_texto = models.CharField(max_length=7, default='#333333', help_text="Color del Texto (Hex)")

    cuerpo_certificado = models.TextField(
        default="Por haber completado satisfactoriamente el curso de capacitación continua, demostrando compromiso y excelencia académica. Por su participación en el seminario '{curso}', contribuyendo de manera activa y profesional al desarrollo de nuevas competencias.",
        help_text="Texto principal del certificado"
    )

    # Firma 1 (Principal - e.g., Rector)
    firma_inst_1 = models.ForeignKey('core.FirmaInstitucional', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma1', verbose_name="Firma Institucional 1")
    nombre_firma_1 = models.CharField(max_length=100, blank=True, default="", verbose_name="Nombre Autoridad 1")
    cargo_firma_1 = models.CharField(max_length=100, blank=True, default="", verbose_name="Cargo Autoridad 1")
    imagen_firma_1 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 1 (Base64)")

    # Firma 2 (Secundaria - e.g., Decano/Vicerrectora)
    firma_inst_2 = models.ForeignKey('core.FirmaInstitucional', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma2', verbose_name="Firma Institucional 2")
    nombre_firma_2 = models.CharField(max_length=100, blank=True, default="", verbose_name="Nombre Autoridad 2")
    cargo_firma_2 = models.CharField(max_length=100, blank=True, default="", verbose_name="Cargo Autoridad 2")
    imagen_firma_2 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 2 (Base64)")

    # Firma 3 (Opcional)
    firma_inst_3 = models.ForeignKey('core.FirmaInstitucional', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma3', verbose_name="Firma Institucional 3")
    nombre_firma_3 = models.CharField(max_length=100, blank=True, verbose_name="Nombre Autoridad 3")
    cargo_firma_3 = models.CharField(max_length=100, blank=True, verbose_name="Cargo Autoridad 3")
    imagen_firma_3 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 3 (Base64)")

    # Firma 4 (Opcional)
    firma_inst_4 = models.ForeignKey('core.FirmaInstitucional', on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes_firma4', verbose_name="Firma Institucional 4")
    nombre_firma_4 = models.CharField(max_length=100, blank=True, verbose_name="Nombre Autoridad 4")
    cargo_firma_4 = models.CharField(max_length=100, blank=True, verbose_name="Cargo Autoridad 4")
    imagen_firma_4 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 4 (Base64)")

    # Header Logos (Opcional, hasta 3)
    logo_header_1 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 1")
    logo_header_2 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 2")
    logo_header_3 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 3")

    posicion_firmas = models.FloatField(
        default=4.2,
        verbose_name='Posición vertical de firmas (cm)',
        help_text='Distancia desde el borde inferior. Mayor = más arriba.'
    )

    objects = LoteManager()

    class Meta:
        verbose_name = 'Lote de Certificados'
        verbose_name_plural = 'Lotes de Certificados'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['activo', '-fecha_creacion']),
            models.Index(fields=['facultad']),
        ]

    def __str__(self):
        return self.nombre_lote

    @property
    def firmas_activas(self):
        """Lista de firmas configuradas (1..4), ignorando slots vacíos.

        Una firma se considera activa si tiene `firma_inst_X` o si tiene
        `nombre_firma_X` (firma custom). Usado por las plantillas PDF.
        """
        firmas = []
        for i in range(1, 5):
            inst = getattr(self, f'firma_inst_{i}')
            nombre = getattr(self, f'nombre_firma_{i}', '') or ''
            if inst:
                firmas.append({
                    'slot': i, 'nombre': inst.nombre, 'cargo': inst.cargo,
                    'imagen': inst.imagen,
                })
            elif nombre.strip():
                firmas.append({
                    'slot': i, 'nombre': nombre,
                    'cargo': getattr(self, f'cargo_firma_{i}', '') or '',
                    'imagen': getattr(self, f'imagen_firma_{i}', '') or '',
                })
        return firmas


class Certificado(TimestampedModel):
    """Certificado individual emitido a un participante por un curso específico.

    Los campos personales (cédula, nombres, email) se congelan en el momento
    de emisión: aunque el Participante se actualice después, el certificado
    conserva los datos originales (auditoría + valor legal).
    """
    lote = models.ForeignKey(LoteCertificados, on_delete=models.CASCADE, related_name='certificados')
    participante = models.ForeignKey(
        'core.Participante', on_delete=models.SET_NULL,
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
    hash_verificacion = models.CharField(
        max_length=100, unique=True, default=uuid.uuid4, db_index=True,
    )
    pdf_generado = models.FileField(upload_to='certificados_pdf/', null=True, blank=True)

    # Metricas
    descargas_count = models.IntegerField(default=0)
    veces_buscado = models.IntegerField(default=0)
    fecha_ultima_descarga = models.DateTimeField(null=True, blank=True)

    objects = CertificadoManager()

    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(horas__gte=0),
                name='certificado_horas_no_negativas',
            ),
        ]
        indexes = [
            models.Index(fields=['lote', '-created_at']),
            models.Index(fields=['cedula', 'email']),
        ]

    def __str__(self):
        return f"{self.cedula} - {self.curso}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def fue_descargado(self):
        return self.descargas_count > 0
