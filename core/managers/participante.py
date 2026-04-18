from django.db import models
from django.db.models import Q


class ParticipanteQuerySet(models.QuerySet):
    def search(self, query: str):
        query = (query or '').strip()
        if not query:
            return self.none()
        tokens = query.split()
        q = Q(cedula__icontains=query) | Q(email__icontains=query)
        for t in tokens:
            q |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)
        return self.filter(q).distinct()

    def lideres(self):
        return self.filter(es_lider=True)

    def with_counts(self):
        return self.annotate(certificados_total=models.Count('certificados', distinct=True))


class ParticipanteManager(models.Manager):
    def get_queryset(self):
        return ParticipanteQuerySet(self.model, using=self._db)

    def search(self, q):
        return self.get_queryset().search(q)

    def lideres(self):
        return self.get_queryset().lideres()
