def sesion_payload(sesion):
    """Data de la sesión para respuestas tras inscripción."""
    return {
        'titulo': sesion.titulo or sesion.dia_semana,
        'fecha': sesion.fecha.strftime('%d/%m/%Y'),
        'horario': sesion.label,
        'lugar': sesion.lugar,
        'modalidad': sesion.modalidad,
        'plataforma': sesion.plataforma_display_safe if sesion.es_virtual else '',
        'enlace_virtual': sesion.enlace_virtual if sesion.es_virtual else '',
    }
