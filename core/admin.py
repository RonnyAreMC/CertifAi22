from django.contrib import admin
from core.models import Usuario, SolicitudAcceso, SesionAsistencia, RegistroAsistencia, ConfirmacionAsistencia, Participante, LandingBloque


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'rol', 'facultad', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'activo', 'fecha_creacion')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        ('Información Personal', {'fields': ('username', 'email', 'first_name', 'last_name', 'telefono')}),
        ('Institución', {'fields': ('facultad', 'rol')}),
        ('Estado', {'fields': ('activo', 'is_staff', 'is_superuser')}),
    )
    readonly_fields = ('fecha_creacion', 'ultimo_acceso')


@admin.register(SolicitudAcceso)
class SolicitudAccesoAdmin(admin.ModelAdmin):
    list_display = ('get_solicitante', 'email', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud', 'facultad')
    search_fields = ('nombres', 'apellidos', 'email')
    readonly_fields = ('fecha_solicitud', 'fecha_respuesta', 'usuario_creado')
    fieldsets = (
        ('Solicitud', {'fields': ('nombres', 'apellidos', 'email', 'telefono')}),
        ('Institución', {'fields': ('facultad',)}),
        ('Respuesta', {'fields': ('estado', 'usuario_creado', 'aprobado_por', 'motivo_rechazo', 'fecha_respuesta')}),
        ('Auditoría', {'fields': ('fecha_solicitud',), 'classes': ('collapse',)}),
    )
    
    def get_solicitante(self, obj):
        return f"{obj.nombres} {obj.apellidos}"
    get_solicitante.short_description = "Solicitante"
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            # Si el objeto ya existe, no permitir editar campos importantes
            return self.readonly_fields + ['nombres', 'apellidos', 'email', 'facultad']
        return self.readonly_fields


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cedula', 'email', 'celular', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('cedula', 'email', 'nombres', 'apellidos')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SesionAsistencia)
class SesionAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'lugar', 'fecha', 'capacidad', 'confirmados_count', 'activa')
    list_filter = ('fecha', 'activa', 'lote')
    search_fields = ('titulo', 'lugar', 'lote__nombre_lote')
    readonly_fields = ('codigo_qr', 'confirmados_count', 'created_at')


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_participante_info', 'sesion', 'fecha_registro')
    list_filter = ('sesion__fecha', 'fecha_registro')
    search_fields = ('participante__cedula', 'participante__email', 'participante__nombres')
    readonly_fields = ('fecha_registro',)

    def get_participante_info(self, obj):
        if obj.participante:
            return f"{obj.participante.nombres} {obj.participante.apellidos} ({obj.participante.cedula})"
        if obj.certificado:
            return f"{obj.certificado.nombres} {obj.certificado.apellidos} ({obj.certificado.cedula})"
        return "?"
    get_participante_info.short_description = "Participante"


@admin.register(ConfirmacionAsistencia)
class ConfirmacionAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_participante_info', 'sesion', 'confirmado', 'bloqueado')
    list_filter = ('confirmado', 'bloqueado', 'sesion__fecha')
    search_fields = ('participante__cedula', 'participante__email', 'participante__nombres')
    actions = ['marcar_bloqueado', 'desmarcar_bloqueado']

    def get_participante_info(self, obj):
        if obj.participante:
            return f"{obj.participante.nombres} {obj.participante.apellidos}"
        if obj.certificado:
            return f"{obj.certificado.nombres} {obj.certificado.apellidos}"
        return "?"
    get_participante_info.short_description = "Participante"
    
    def marcar_bloqueado(self, request, queryset):
        queryset.update(bloqueado=True)
    marcar_bloqueado.short_description = "Marcar como bloqueado"
    
    def desmarcar_bloqueado(self, request, queryset):
        queryset.update(bloqueado=False)
    desmarcar_bloqueado.short_description = "Desmarcar como bloqueado"


@admin.register(LandingBloque)
class LandingBloqueAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tipo', 'estilo', 'orden', 'activo')
    list_filter = ('tipo', 'activo')
    list_editable = ('orden', 'activo')
    ordering = ('orden',)
