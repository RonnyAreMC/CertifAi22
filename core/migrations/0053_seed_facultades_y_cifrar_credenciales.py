"""Seed inicial de Facultades + cifrado de credenciales existentes.

Se ejecuta después de 0052 (que creó la tabla Facultad y cambió los campos
de credenciales a Encrypted*Field).

Idempotente:
- Facultades: usa get_or_create por código.
- Credenciales: el decrypt detecta valores en plain text (legacy) y los
  devuelve tal cual; el siguiente save los re-cifrará. Para forzar el
  re-cifrado en la migración, leemos cada fila, las re-asignamos y
  guardamos — la EncryptedField cifra al save().
"""
from django.db import migrations


FACULTADES_SEED = [
    ('FACI',     'FACI - Ingeniería',              1),
    ('FACS',     'FACS - Salud',                   2),
    ('FACE',     'FACE - Educación',               3),
    ('FACSECYD', 'FACSECYD - Ciencias Sociales',   4),
    ('POSGRADO', 'Posgrado / Otra',                5),
]


def seed_facultades(apps, schema_editor):
    Facultad = apps.get_model('core', 'Facultad')
    for codigo, nombre, orden in FACULTADES_SEED:
        Facultad.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'orden': orden, 'activa': True},
        )


def reverse_facultades(apps, schema_editor):
    Facultad = apps.get_model('core', 'Facultad')
    Facultad.objects.filter(codigo__in=[c for c, _, _ in FACULTADES_SEED]).delete()


def reencrypt_credentials(apps, schema_editor):
    """Re-guarda cada GoogleCredential y AIConfig para forzar cifrado.

    Si el valor estaba en plain text, queda cifrado en la BD tras este save.
    Si ya estaba cifrado, decrypt → re-encrypt = mismo plain text.
    """
    GoogleCredential = apps.get_model('core', 'GoogleCredential')
    AIConfig = apps.get_model('core', 'AIConfig')

    # OJO: apps.get_model devuelve modelos historicos (sin los Encrypted*Field).
    # Para cifrar usamos el modelo real importando aquí.
    from core.models import GoogleCredential as RealGC, AIConfig as RealAI

    for obj in RealGC.objects.all():
        obj.save()
    for obj in RealAI.objects.all():
        obj.save()


def noop(apps, schema_editor):
    """Reverse: no hay forma de descifrar masivamente sin perder integridad."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_facultad_remove_sesionasistencia_dia_semana_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_facultades, reverse_facultades),
        migrations.RunPython(reencrypt_credentials, noop),
    ]
