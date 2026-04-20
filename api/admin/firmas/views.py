from rest_framework import serializers, permissions

from core.models import FirmaInstitucional
from api.common.viewsets import AuditedModelViewSet


class FirmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirmaInstitucional
        fields = ['id', 'nombre', 'cargo', 'imagen', 'activa', 'orden', 'fecha_creacion']
        read_only_fields = ('fecha_creacion',)


class FirmaViewSet(AuditedModelViewSet):
    queryset = FirmaInstitucional.objects.all()
    serializer_class = FirmaSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ['nombre', 'cargo']
    ordering_fields = ['orden', 'nombre']
    ordering = ['orden', 'nombre']

    audit_verbose_name = 'firma institucional'

    def audit_detail(self, instance, action):
        return f'Firma #{instance.pk} ({instance.nombre} - {instance.cargo})'
