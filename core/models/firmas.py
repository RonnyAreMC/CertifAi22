"""Modelos de firmas institucionales y diseño global de certificados."""
from django.db import models

from core.base.models import SingletonModel

from ._choices import Plantilla


class FirmaInstitucional(models.Model):
    """Firma de autoridad (rector, decano, etc.) reutilizable en certificados."""
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


class DisenoGlobal(SingletonModel):
    """Configuración de diseño GLOBAL para todos los certificados.

    Invariante singleton: siempre `pk=1`. Usa `DisenoGlobal.get_solo()`
    para obtener/crear la instancia. Solo superadmin puede modificarlo.

    Todos los lotes con `personalizar_diseno=False` heredan estos valores
    vía `core.services.pdf._diseno._apply_diseno_global`.
    """
    plantilla = models.CharField(max_length=20, choices=Plantilla.choices, default=Plantilla.CLASICO)
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

    posicion_firmas = models.FloatField(
        default=4.2,
        verbose_name='Posición vertical de firmas (cm)',
        help_text='Distancia desde el borde inferior en centímetros. Mayor = más arriba.'
    )

    # Per-signature adjustments (offset_y in cm, escala in %)
    firma_1_offset_y = models.FloatField(default=0, help_text='Ajuste vertical firma 1 (cm)')
    firma_1_escala = models.FloatField(default=100, help_text='Escala firma 1 (%)')
    firma_2_offset_y = models.FloatField(default=0, help_text='Ajuste vertical firma 2 (cm)')
    firma_2_escala = models.FloatField(default=100, help_text='Escala firma 2 (%)')
    firma_3_offset_y = models.FloatField(default=0, help_text='Ajuste vertical firma 3 (cm)')
    firma_3_escala = models.FloatField(default=100, help_text='Escala firma 3 (%)')
    firma_4_offset_y = models.FloatField(default=0, help_text='Ajuste vertical firma 4 (cm)')
    firma_4_escala = models.FloatField(default=100, help_text='Escala firma 4 (%)')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diseño Global'
        verbose_name_plural = 'Diseño Global'

    def __str__(self):
        return f"Diseño Global ({self.get_plantilla_display()})"
