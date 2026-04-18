from django.db import models


class TimestampedModel(models.Model):
    """Mixin abstracto con created_at / updated_at."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """Base para modelos con una sola instancia (ej. DisenoGlobal)."""

    class Meta:
        abstract = True

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
