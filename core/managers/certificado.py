from django.db import models
from django.db.models import Q


class CertificadoQuerySet(models.QuerySet):
    def search(self, query: str):
        """Búsqueda de certificados.

        Reglas:
        - Si la query es un match EXACTO de cédula / email / hash → devuelve esos.
        - Si no, split en tokens y requiere que CADA token aparezca en nombres
          o apellidos (AND entre tokens, OR dentro de cada campo).
        """
        query = (query or '').strip()
        if not query:
            return self.none()

        exact_filter = (
            Q(cedula__iexact=query)
            | Q(email__iexact=query.lower())
            | Q(hash_verificacion__iexact=query)
        )

        tokens = [t for t in query.split() if t]
        name_filter = Q()
        for t in tokens:
            name_filter &= (
                Q(nombres__icontains=t)
                | Q(apellidos__icontains=t)
                | Q(cedula__icontains=t)
                | Q(email__icontains=t)
            )

        # Si solo había un token que NO es exact match, name_filter se aplica.
        # Si había varios, cada uno DEBE matchear.
        combined = exact_filter | name_filter if tokens else exact_filter
        return self.filter(combined).distinct()

    def with_relations(self):
        return self.select_related('lote', 'participante')

    def downloaded(self):
        return self.filter(descargas_count__gt=0)

    def by_faculty(self, faculty_code: str):
        return self.filter(lote__facultad=faculty_code)

    def deduped_by_person_course(self):
        """Dedupe por (cedula, curso) → devuelve el más reciente de cada par.

        Implementado con subquery (compatible con SQLite y PostgreSQL).
        """
        from django.db.models import Max
        latest_ids = (
            self.values('cedula', 'curso')
            .annotate(latest_id=Max('id'))
            .values_list('latest_id', flat=True)
        )
        return self.filter(id__in=list(latest_ids))


class CertificadoManager(models.Manager):
    def get_queryset(self):
        return CertificadoQuerySet(self.model, using=self._db)

    def search(self, q):
        return self.get_queryset().search(q)

    def downloaded(self):
        return self.get_queryset().downloaded()

    def with_relations(self):
        return self.get_queryset().with_relations()

    def deduped_by_person_course(self):
        return self.get_queryset().deduped_by_person_course()
