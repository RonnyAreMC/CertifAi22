from django.db import models
from django.db.models import Q


class CertificadoQuerySet(models.QuerySet):
    def search(self, query: str):
        query = (query or '').strip()
        if not query:
            return self.none()
        tokens = query.split()
        q = Q(cedula__icontains=query) | Q(email__icontains=query) | Q(hash_verificacion__iexact=query)
        for t in tokens:
            q |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)
        return self.filter(q).distinct()

    def with_relations(self):
        return self.select_related('lote', 'participante')

    def downloaded(self):
        return self.filter(descargas_count__gt=0)

    def by_faculty(self, faculty_code: str):
        return self.filter(lote__facultad=faculty_code)


class CertificadoManager(models.Manager):
    def get_queryset(self):
        return CertificadoQuerySet(self.model, using=self._db)

    def search(self, q):
        return self.get_queryset().search(q)

    def downloaded(self):
        return self.get_queryset().downloaded()

    def with_relations(self):
        return self.get_queryset().with_relations()
