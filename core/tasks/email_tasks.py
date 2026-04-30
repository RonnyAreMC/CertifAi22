"""Tareas Celery para envío masivo de correos transaccionales.

El uso típico es disparar `send_certificate_issued_bulk.delay(lote_id)` cuando
se genera un lote — la response del request al admin no espera el envío de
N correos vía Gmail API.

En desarrollo sin Redis, `CELERY_TASK_ALWAYS_EAGER=True` hace que la task
corra inmediatamente sincrónica (mismo comportamiento que antes).
"""
from __future__ import annotations

import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from core.models import Certificado, LoteCertificados, Participante
from core.services.email import sender as email_sender

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def send_certificate_issued_bulk(self, lote_id: int) -> dict:
    """Envía notificación de certificado emitido a TODOS los certs del lote.

    Returns:
        dict con `sent`, `failed`, `total`, `lote_id`.
    """
    try:
        lote = LoteCertificados.objects.get(pk=lote_id)
    except LoteCertificados.DoesNotExist:
        logger.warning('Lote %s no existe — task abortada', lote_id)
        return {'sent': 0, 'failed': 0, 'total': 0, 'lote_id': lote_id, 'error': 'lote_not_found'}

    sesion = getattr(lote, 'sesionasistencia', None) or lote.sesiones.first() if hasattr(lote, 'sesiones') else None
    if sesion is None:
        # Caso fallback: el lote no tiene sesión asociada (lote subido manualmente).
        # No mandamos correos porque no tenemos contexto del evento.
        logger.info('Lote %s no tiene sesión asociada — sin envío de correos', lote_id)
        return {'sent': 0, 'failed': 0, 'total': 0, 'lote_id': lote_id, 'error': 'no_sesion'}

    certs = list(
        Certificado.objects
            .filter(lote=lote)
            .select_related('participante')
    )
    sent = 0
    failed = 0
    try:
        for cert in certs:
            ok = email_sender.send_certificate_issued(
                certificado=cert,
                sesion=sesion,
                participante=cert.participante,
                request=None,  # sin request, los URLs usan SITE_URL del settings
            )
            if ok:
                sent += 1
            else:
                failed += 1
    except SoftTimeLimitExceeded:
        logger.warning('Soft time limit alcanzado en lote %s · sent=%s failed=%s', lote_id, sent, failed)
        # Devolvemos parcial — los certs ya enviados no se reenvían en retry
        return {'sent': sent, 'failed': failed, 'total': len(certs), 'lote_id': lote_id, 'partial': True}

    logger.info('Bulk email lote %s · sent=%s failed=%s total=%s', lote_id, sent, failed, len(certs))
    return {'sent': sent, 'failed': failed, 'total': len(certs), 'lote_id': lote_id}


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email_async(participante_id: int) -> bool:
    p = Participante.objects.get(pk=participante_id)
    return email_sender.send_welcome_email(p)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_event_inscription_async(participante_id: int, sesion_id: int) -> bool:
    from core.models import SesionAsistencia
    p = Participante.objects.get(pk=participante_id)
    s = SesionAsistencia.objects.get(pk=sesion_id)
    return email_sender.send_event_inscription(p, s)
