from django.contrib import admin, messages
from core.models import (
    Usuario, SolicitudAcceso, SesionAsistencia, RegistroAsistencia,
    ConfirmacionAsistencia, ResumenSesion, IntentoCuestionario,
)


@admin.register(IntentoCuestionario)
class IntentoCuestionarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'participante', 'sesion', 'correctas', 'total', 'porcentaje', 'tiempo_total_seg', 'created_at')
    list_filter = ('sesion', 'created_at')
    search_fields = ('participante__email', 'participante__cedula', 'sesion__titulo')
    readonly_fields = ('created_at', 'porcentaje')


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


@admin.register(SesionAsistencia)
class SesionAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'fecha', 'capacidad', 'confirmados_count', 'activa')
    list_filter = ('fecha', 'activa', 'lote')
    search_fields = ('titulo', 'lote__nombre_lote')
    readonly_fields = ('codigo_qr', 'confirmados_count', 'created_at')


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_certificado_info', 'sesion', 'fecha_registro')
    list_filter = ('sesion__fecha', 'fecha_registro')
    search_fields = ('certificado__cedula', 'certificado__email')
    readonly_fields = ('fecha_registro',)
    
    def get_certificado_info(self, obj):
        return f"{obj.certificado.nombres} {obj.certificado.apellidos} ({obj.certificado.cedula})"
    get_certificado_info.short_description = "Participante"


@admin.register(ConfirmacionAsistencia)
class ConfirmacionAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_certificado_info', 'sesion', 'confirmado', 'bloqueado')
    list_filter = ('confirmado', 'bloqueado', 'sesion__fecha')
    search_fields = ('certificado__cedula', 'certificado__email')
    actions = ['marcar_bloqueado', 'desmarcar_bloqueado']
    
    def get_certificado_info(self, obj):
        return f"{obj.certificado.nombres} {obj.certificado.apellidos}"
    get_certificado_info.short_description = "Participante"
    
    def marcar_bloqueado(self, request, queryset):
        queryset.update(bloqueado=True)
    marcar_bloqueado.short_description = "Marcar como bloqueado"
    
    def desmarcar_bloqueado(self, request, queryset):
        queryset.update(bloqueado=False)
    desmarcar_bloqueado.short_description = "Desmarcar como bloqueado"


@admin.register(ResumenSesion)
class ResumenSesionAdmin(admin.ModelAdmin):
    list_display = (
        'sesion', 'estado', 'transcript_chars', 'duracion_minutos',
        'ai_model', 'procesado_at', 'created_at',
    )
    list_filter = ('estado', 'ai_model', 'created_at')
    search_fields = ('sesion__titulo', 'drive_file_name', 'drive_file_id')
    readonly_fields = (
        'created_at', 'procesado_at',
        'transcript_chars', 'duracion_minutos',
        'ai_input_tokens', 'ai_output_tokens',
    )
    actions = ['reprocesar', 'limpiar_transcript_raw']

    fieldsets = (
        ('Sesión', {'fields': ('sesion', 'estado', 'error_msg')}),
        ('Origen Drive', {'fields': (
            'drive_file_id', 'drive_file_name', 'transcript_chars',
        )}),
        ('Resultado IA', {'fields': (
            'resumen_md', 'puntos_clave', 'proximos_pasos', 'cuestionario',
            'duracion_minutos',
        )}),
        ('Auditoría', {'fields': (
            'ai_model', 'ai_input_tokens', 'ai_output_tokens',
            'created_at', 'procesado_at',
        )}),
        ('Transcript crudo (puede ser largo)', {
            'classes': ('collapse',),
            'fields': ('transcript_raw',),
        }),
    )

    def reprocesar(self, request, queryset):
        from core.tasks.transcript_tasks import procesar_transcript_sesion
        encolados = 0
        for resumen in queryset:
            procesar_transcript_sesion.delay(resumen.sesion_id)
            encolados += 1
        self.message_user(
            request, f'Encolado reprocesamiento de {encolados} resumen(es).',
            level=messages.INFO,
        )
    reprocesar.short_description = 'Reprocesar transcript con IA'

    def limpiar_transcript_raw(self, request, queryset):
        """Libera espacio en DB borrando el texto crudo (deja resumen + cuestionario)."""
        n = 0
        for r in queryset:
            r.transcript_raw = ''
            r.save(update_fields=['transcript_raw'])
            n += 1
        self.message_user(
            request, f'Transcript crudo borrado en {n} resumen(es).',
            level=messages.INFO,
        )
    limpiar_transcript_raw.short_description = 'Borrar transcript crudo (mantiene resumen)'
