from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.conf import settings

class Usuario(AbstractUser):
    """Usuario del sistema (solo administradores)"""
    ROLES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='admin')
    facultad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"

class LoteCertificados(models.Model):
    nombre_lote = models.CharField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    archivo_excel = models.FileField(upload_to='lotes_excel/')
    administrador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    activo = models.BooleanField(default=True)
    
    FACULTADES = [
        ('FACI', 'FACI - Ingeniería'),
        ('FACS', 'FACS - Salud'),
        ('FACE', 'FACE - Educación'),
        ('FACSECYD', 'FACSECYD - Ciencias Sociales'),
        ('POSGRADO', 'Posgrado / Otra'),
    ]
    facultad = models.CharField(max_length=20, choices=FACULTADES, default='FACI', db_index=True)
    
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
        default="Por haber completado satisfactoriamente el curso de capacitación continua, demostrando compromiso y excelencia académica.",
        help_text="Texto principal del certificado"
    )
    
    # Firma 1 (Principal - e.g., Rector)
    nombre_firma_1 = models.CharField(max_length=100, default="Ph.D. Fabricio Guevara Viejó", verbose_name="Nombre Autoridad 1")
    cargo_firma_1 = models.CharField(max_length=100, default="RECTOR UNEMI", verbose_name="Cargo Autoridad 1")
    imagen_firma_1 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 1 (Base64)")
    
    # Firma 2 (Secundaria - e.g., Decano/Vicerrectora)
    nombre_firma_2 = models.CharField(max_length=100, default="Ph.D. Jesennia Cárdenas Cobo", verbose_name="Nombre Autoridad 2", blank=True)
    cargo_firma_2 = models.CharField(max_length=100, default="VICERRECTORA ACADÉMICA", verbose_name="Cargo Autoridad 2", blank=True)
    imagen_firma_2 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 2 (Base64)")

    # Firma 3 (Opcional)
    nombre_firma_3 = models.CharField(max_length=100, blank=True, verbose_name="Nombre Autoridad 3")
    cargo_firma_3 = models.CharField(max_length=100, blank=True, verbose_name="Cargo Autoridad 3")
    imagen_firma_3 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 3 (Base64)")

    # Firma 4 (Opcional)
    nombre_firma_4 = models.CharField(max_length=100, blank=True, verbose_name="Nombre Autoridad 4")
    cargo_firma_4 = models.CharField(max_length=100, blank=True, verbose_name="Cargo Autoridad 4")
    imagen_firma_4 = models.TextField(null=True, blank=True, verbose_name="Firma Autoridad 4 (Base64)")

    # Header Logos (Opcional, hasta 3)
    logo_header_1 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 1")
    logo_header_2 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 2")
    logo_header_3 = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo Cabecera 3")

    def __str__(self):
        return self.nombre_lote

class Certificado(models.Model):
    lote = models.ForeignKey(LoteCertificados, on_delete=models.CASCADE, related_name='certificados')
    cedula = models.CharField(max_length=20, db_index=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=200, db_index=True)
    
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
