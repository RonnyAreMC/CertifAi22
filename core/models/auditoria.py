"""Modelo de registro de auditoría para acciones administrativas."""
from django.db import models
from django.conf import settings


class Auditoria(models.Model):
    """Log de acciones administrativas (CREAR, EDITAR, ELIMINAR)."""
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
