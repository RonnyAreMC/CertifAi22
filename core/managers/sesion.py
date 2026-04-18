from django.db import models
from django.db.models import Count
from django.utils import timezone


class SesionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(activa=True)

    def upcoming(self):
        return self.filter(activa=True, fecha__gte=timezone.now().date())

    def past(self):
        return self.filter(fecha__lt=timezone.now().date())

    def with_stats(self):
        return self.annotate(
            total_confirmados=Count('confirmaciones', distinct=True),
            total_asistentes=Count('registros', distinct=True),
        )


class SesionManager(models.Manager):
    def get_queryset(self):
        return SesionQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def upcoming(self):
        return self.get_queryset().upcoming()

    def past(self):
        return self.get_queryset().past()

    def with_stats(self):
        return self.get_queryset().with_stats()
