from django.db import models
from django.db.models import Count


class LoteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(activo=True)

    def with_stats(self):
        return self.annotate(
            total_certificados=Count('certificados', distinct=True),
        )

    def by_faculty(self, code: str):
        return self.filter(facultad=code)


class LoteManager(models.Manager):
    def get_queryset(self):
        return LoteQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_stats(self):
        return self.get_queryset().with_stats()
