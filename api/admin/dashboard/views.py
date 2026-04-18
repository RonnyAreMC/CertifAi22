from datetime import timedelta

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Certificado, LoteCertificados, Auditoria


class AdminDashboardView(APIView):
    """GET /api/v1/admin/dashboard/ → todas las métricas del dashboard admin."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        total_certificados = Certificado.objects.count()
        total_descargas = Certificado.objects.aggregate(total=Sum('descargas_count'))['total'] or 0
        total_busquedas = Certificado.objects.aggregate(total=Sum('veces_buscado'))['total'] or 0
        total_lotes = LoteCertificados.objects.count()

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

        # Certificados emitidos últimos 14 días
        last_14_days = timezone.now().date() - timedelta(days=14)
        stats_daily = list(
            Certificado.objects.filter(created_at__gte=last_14_days)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        labels_daily = [i['date'].strftime('%d/%m') for i in stats_daily]
        data_daily = [i['count'] for i in stats_daily]

        return Response({
            'totals': {
                'certificados': total_certificados,
                'descargas': total_descargas,
                'busquedas': total_busquedas,
                'lotes': total_lotes,
            },
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
            },
        })
