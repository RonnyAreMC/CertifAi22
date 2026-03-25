from django.db import migrations


def crear_firmas_default(apps, schema_editor):
    FirmaInstitucional = apps.get_model('core', 'FirmaInstitucional')
    defaults = [
        {'cargo': 'RECTOR UNEMI', 'orden': 1},
        {'cargo': 'VICERRECTORA ACADÉMICA', 'orden': 2},
        {'cargo': 'PRESIDENTE FEUE', 'orden': 3},
        {'cargo': 'PRESIDENTA OCS', 'orden': 4},
    ]
    for d in defaults:
        if not FirmaInstitucional.objects.filter(cargo=d['cargo']).exists():
            FirmaInstitucional.objects.create(
                nombre='',
                cargo=d['cargo'],
                imagen='',
                activa=True,
                orden=d['orden'],
            )


def borrar_firmas_default(apps, schema_editor):
    FirmaInstitucional = apps.get_model('core', 'FirmaInstitucional')
    FirmaInstitucional.objects.filter(cargo__in=[
        'RECTOR UNEMI', 'VICERRECTORA ACADÉMICA',
        'PRESIDENTE FEUE', 'PRESIDENTA OCS',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_firma_orden_and_defaults'),
    ]

    operations = [
        migrations.RunPython(crear_firmas_default, borrar_firmas_default),
    ]
