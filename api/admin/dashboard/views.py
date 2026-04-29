from datetime import timedelta

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Certificado, LoteCertificados, Auditoria,
    SesionAsistencia, Participante, ConfirmacionAsistencia, SolicitudAcceso,
)


class AdminDashboardView(APIView):
    """GET /api/v1/admin/dashboard/ → todas las métricas del dashboard admin."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        today = now.date()

        total_certificados = Certificado.objects.count()
        total_descargas = Certificado.objects.aggregate(total=Sum('descargas_count'))['total'] or 0
        total_busquedas = Certificado.objects.aggregate(total=Sum('veces_buscado'))['total'] or 0
        total_lotes = LoteCertificados.objects.count()
        total_participantes = Participante.objects.count()
        total_eventos = SesionAsistencia.objects.filter(activa=True).count()
        total_inscripciones = ConfirmacionAsistencia.objects.filter(confirmado=True).count()
        solicitudes_pendientes = SolicitudAcceso.objects.filter(estado='pendiente').count()

        # Lotes recientes
        recent_lotes = list(
            LoteCertificados.objects.order_by('-fecha_creacion')
            .values('id', 'nombre_lote', 'facultad', 'fecha_creacion')[:5]
        )

        # Auditoría reciente
        auditoria = list(
            Auditoria.objects.select_related('usuario')[:10]
            .values('id', 'accion', 'detalle', 'fecha',
                    'usuario__username', 'usuario__first_name', 'usuario__last_name')
        )

        # Distribución por facultad
        stats_facultad = list(
            Certificado.objects.values('lote__facultad')
            .annotate(total=Count('id')).order_by('-total')
        )
        labels_facultad = [i['lote__facultad'] for i in stats_facultad if i['lote__facultad']]
        data_facultad = [i['total'] for i in stats_facultad if i['lote__facultad']]

        # Top 5 lotes por descargas
        top_lotes = list(
            Certificado.objects.values('lote__nombre_lote')
            .annotate(downloads=Sum('descargas_count'))
            .order_by('-downloads')[:5]
        )
        labels_top_lotes = [i['lote__nombre_lote'] for i in top_lotes]
        data_top_lotes = [i['downloads'] or 0 for i in top_lotes]

        # Próximos eventos (próximos 7 días)
        upcoming_sessions_qs = (
            SesionAsistencia.objects
            .filter(activa=True, fecha__gte=today, fecha__lte=today + timedelta(days=7))
            .annotate(num_inscritos=Count('confirmaciones'))
            .order_by('fecha', 'hora_inicio')[:5]
        )
        upcoming_sessions = [
            {
                'id': s.id,
                'titulo': s.titulo or s.dia_semana,
                'fecha': s.fecha.isoformat(),
                'fecha_display': s.fecha.strftime('%d/%m'),
                'dia_semana': s.dia_semana,
                'hora_inicio': s.hora_inicio.strftime('%H:%M'),
                'hora_fin': s.hora_fin.strftime('%H:%M'),
                'modalidad': s.modalidad,
                'lugar': s.lugar,
                'inscritos': s.num_inscritos,
                'capacidad': s.capacidad,
                'es_hoy': s.fecha == today,
            }
            for s in upcoming_sessions_qs
        ]

        # ── Series diarias últimos 14 días para sparklines/charts ──
        last_14_days = today - timedelta(days=14)

        def _serie_diaria_count(qs, date_field: str):
            """Devuelve [count_dia_-13, ..., count_hoy] como lista de 14 items."""
            counts_by_date = dict(
                qs.filter(**{f'{date_field}__date__gte': last_14_days})
                .annotate(d=TruncDate(date_field))
                .values('d').annotate(c=Count('id')).values_list('d', 'c')
            )
            out = []
            for offset in range(13, -1, -1):
                d = today - timedelta(days=offset)
                out.append(counts_by_date.get(d, 0))
            return out

        labels_daily = [
            (today - timedelta(days=offset)).strftime('%d/%m')
            for offset in range(13, -1, -1)
        ]
        data_daily = _serie_diaria_count(Certificado.objects.all(), 'created_at')
        data_inscripciones_daily = _serie_diaria_count(
            ConfirmacionAsistencia.objects.filter(confirmado=True), 'fecha_confirmacion'
        )
        data_eventos_daily = _serie_diaria_count(
            SesionAsistencia.objects.filter(activa=True), 'created_at'
        )

        return Response({
            'totals': {
                'certificados': total_certificados,
                'descargas': total_descargas,
                'busquedas': total_busquedas,
                'lotes': total_lotes,
                'participantes': total_participantes,
                'eventos_activos': total_eventos,
                'inscripciones': total_inscripciones,
                'solicitudes_pendientes': solicitudes_pendientes,
            },
            'upcoming_sessions': upcoming_sessions,
            'recent_lotes': recent_lotes,
            'auditoria': [
                {
                    'id': a['id'],
                    'accion': a['accion'],
                    'detalle': a['detalle'],
                    'fecha': a['fecha'].isoformat(),
                    'usuario_username': a['usuario__username'],
                    'usuario_nombre': f"{a['usuario__first_name']} {a['usuario__last_name']}".strip(),
                }
                for a in auditoria
            ],
            'charts': {
                'facultad': {'labels': labels_facultad, 'data': data_facultad},
                'top_lotes': {'labels': labels_top_lotes, 'data': data_top_lotes},
                'daily': {'labels': labels_daily, 'data': data_daily},
                'daily_inscripciones': data_inscripciones_daily,
                'daily_eventos': data_eventos_daily,
            },
        })
