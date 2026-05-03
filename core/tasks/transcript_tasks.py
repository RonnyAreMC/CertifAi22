"""Tareas Celery del pipeline Drive → transcript → IA → resumen.

Flujo de la task `procesar_transcript_sesion(sesion_id)`:

  1. Carga la sesión + crea/recupera el ResumenSesion vinculado.
  2. Estado=BUSCANDO → busca el transcript en Drive.
     - Si no aparece todavía → estado=SIN_TRANSCRIPT, sale (puede reintentarse).
  3. Estado=PROCESANDO → descarga el doc, lo pasa a texto plano.
  4. Llama al pipeline IA (Claude) → resumen + cuestionario.
  5. Estado=LISTO → guarda todo en el modelo.

Si algo falla, deja estado=FALLIDO con `error_msg` para auditoría.
Ningún error de IA o Drive debe matar al worker — todo se captura.
"""
from __future__ import annotations

import logging
import traceback
from datetime import datetime

from celery import shared_task
from django.utils import timezone

from core.models import EstadoProcesamiento, ResumenSesion, SesionAsistencia
from core.services.ai.transcript_summary import summarize_transcript
from core.services.meet.drive_client import find_transcript_for_session
from core.services.meet.transcript_parser import (
    estimate_duration_minutes,
    fetch_transcript_text,
)


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(),  # gestionamos errores nosotros — no auto-retry ciego
    max_retries=0,
)
def procesar_transcript_sesion(self, sesion_id: int) -> dict:
    """Procesa el transcript de una sesión: Drive → texto → IA → DB.

    Idempotente: si ya existe un ResumenSesion en estado LISTO, no hace nada.
    Si está FALLIDO o SIN_TRANSCRIPT, lo reintenta desde cero.
    """
    try:
        sesion = SesionAsistencia.objects.get(pk=sesion_id)
    except SesionAsistencia.DoesNotExist:
        logger.warning('Sesion %s no existe', sesion_id)
        return {'ok': False, 'reason': 'sesion_no_existe', 'sesion_id': sesion_id}

    if not sesion.transcripcion_habilitada:
        logger.info('Sesion %s tiene transcripcion deshabilitada — skip', sesion_id)
        return {'ok': False, 'reason': 'deshabilitada', 'sesion_id': sesion_id}

    resumen, _ = ResumenSesion.objects.get_or_create(sesion=sesion)

    if resumen.estado == EstadoProcesamiento.LISTO:
        logger.info('Sesion %s ya tiene resumen LISTO — skip', sesion_id)
        return {'ok': True, 'reason': 'ya_listo', 'resumen_id': resumen.id}

    # ── 1. Buscar en Drive ──────────────────────────────────────
    resumen.estado = EstadoProcesamiento.BUSCANDO
    resumen.error_msg = ''
    resumen.save(update_fields=['estado', 'error_msg'])

    try:
        tf = find_transcript_for_session(sesion)
    except Exception as e:
        logger.exception('Error buscando transcript para sesion %s', sesion_id)
        resumen.estado = EstadoProcesamiento.FALLIDO
        resumen.error_msg = f'Drive: {e}\n{traceback.format_exc()}'
        resumen.save(update_fields=['estado', 'error_msg'])
        return {'ok': False, 'reason': 'drive_error', 'detail': str(e)}

    if tf is None:
        resumen.estado = EstadoProcesamiento.SIN_TRANSCRIPT
        resumen.save(update_fields=['estado'])
        return {'ok': False, 'reason': 'sin_transcript', 'sesion_id': sesion_id}

    resumen.drive_file_id = tf.file_id
    resumen.drive_file_name = tf.name
    resumen.save(update_fields=['drive_file_id', 'drive_file_name'])

    # ── 2. Parsear el doc → texto plano ──────────────────────────
    try:
        text = fetch_transcript_text(tf.file_id)
    except Exception as e:
        logger.exception('Error parseando transcript %s', tf.file_id)
        resumen.estado = EstadoProcesamiento.FALLIDO
        resumen.error_msg = f'Parser: {e}\n{traceback.format_exc()}'
        resumen.save(update_fields=['estado', 'error_msg'])
        return {'ok': False, 'reason': 'parser_error', 'detail': str(e)}

    if not text.strip():
        resumen.estado = EstadoProcesamiento.SIN_TRANSCRIPT
        resumen.error_msg = 'Drive devolvió transcript vacío'
        resumen.save(update_fields=['estado', 'error_msg'])
        return {'ok': False, 'reason': 'transcript_vacio'}

    duracion = estimate_duration_minutes(text)
    resumen.transcript_raw = text
    resumen.transcript_chars = len(text)
    resumen.duracion_minutos = duracion
    resumen.save(update_fields=[
        'transcript_raw', 'transcript_chars', 'duracion_minutos',
    ])

    # ── 3. IA → resumen estructurado ─────────────────────────────
    resumen.estado = EstadoProcesamiento.PROCESANDO
    resumen.save(update_fields=['estado'])

    try:
        result = summarize_transcript(
            text,
            titulo=sesion.titulo or '',
            fecha=str(sesion.fecha),
            duracion_minutos=duracion,
        )
    except NotImplementedError as e:
        # IA sin configurar — no es un fallo "real", deja todo en FALLIDO
        # con un mensaje claro para que el admin sepa qué activar.
        resumen.estado = EstadoProcesamiento.FALLIDO
        resumen.error_msg = f'IA no configurada: {e}'
        resumen.save(update_fields=['estado', 'error_msg'])
        return {'ok': False, 'reason': 'ia_no_configurada', 'detail': str(e)}
    except Exception as e:
        logger.exception('Error en IA para sesion %s', sesion_id)
        resumen.estado = EstadoProcesamiento.FALLIDO
        resumen.error_msg = f'IA: {e}\n{traceback.format_exc()}'
        resumen.save(update_fields=['estado', 'error_msg'])
        return {'ok': False, 'reason': 'ia_error', 'detail': str(e)}

    # ── 4. Guardar resultado ─────────────────────────────────────
    resumen.resumen_md = result.resumen_md
    resumen.puntos_clave = result.puntos_clave
    resumen.proximos_pasos = result.proximos_pasos
    resumen.cuestionario = result.cuestionario
    resumen.ai_model = result.ai_model
    resumen.ai_input_tokens = result.ai_input_tokens
    resumen.ai_output_tokens = result.ai_output_tokens
    resumen.estado = EstadoProcesamiento.LISTO
    resumen.procesado_at = timezone.now()
    resumen.error_msg = ''
    resumen.save()

    logger.info(
        'Resumen sesion %s LISTO (%d chars transcript → %d puntos clave, %d preguntas)',
        sesion_id, len(text), len(result.puntos_clave), len(result.cuestionario),
    )
    return {
        'ok': True,
        'resumen_id': resumen.id,
        'transcript_chars': len(text),
        'preguntas': len(result.cuestionario),
    }


@shared_task
def procesar_sesiones_pasadas() -> dict:
    """Tarea programada: revisa sesiones de hoy/ayer y dispara procesamiento.

    Pensada para correr cada hora en Celery beat. Procesa sesiones cuyo
    `hora_fin` ya pasó pero todavía no tienen resumen en estado LISTO.
    """
    from datetime import timedelta
    from django.db.models import Q

    ahora = timezone.now()
    desde = (ahora - timedelta(days=2)).date()
    hasta = ahora.date()

    qs = (
        SesionAsistencia.objects
        .filter(transcripcion_habilitada=True)
        .filter(fecha__range=(desde, hasta))
        .filter(
            Q(resumen__isnull=True)
            | Q(resumen__estado__in=[
                EstadoProcesamiento.PENDIENTE,
                EstadoProcesamiento.SIN_TRANSCRIPT,
                EstadoProcesamiento.FALLIDO,
            ])
        )
    )

    encolados = 0
    for sesion in qs:
        # Solo si la hora de fin ya pasó
        fin = datetime.combine(sesion.fecha, sesion.hora_fin)
        fin = timezone.make_aware(fin)
        if sesion.hora_fin < sesion.hora_inicio:
            fin += timezone.timedelta(days=1)
        if fin > ahora:
            continue
        procesar_transcript_sesion.delay(sesion.id)
        encolados += 1

    logger.info('procesar_sesiones_pasadas: %d sesiones encoladas', encolados)
    return {'encoladas': encolados, 'desde': str(desde), 'hasta': str(hasta)}
