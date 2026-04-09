from django.db import migrations, models


def reset_diseno_global(apps, schema_editor):
    """Reinicia el singleton DisenoGlobal a los valores por defecto UNEMI."""
    DisenoGlobal = apps.get_model('core', 'DisenoGlobal')
    FirmaInstitucional = apps.get_model('core', 'FirmaInstitucional')

    diseno, _ = DisenoGlobal.objects.get_or_create(pk=1)

    diseno.plantilla = 'clasico'
    diseno.color_primario = '#162054'
    diseno.color_secundario = '#D4AF37'
    diseno.color_terciario = '#F3F4F6'
    diseno.color_texto = '#333333'
    diseno.cuerpo_certificado = (
        "Por haber completado satisfactoriamente el curso de capacitación continua, "
        "demostrando compromiso y excelencia académica. Por su participación en el "
        "seminario '{curso}', contribuyendo de manera activa y profesional al "
        "desarrollo de nuevas competencias."
    )
    # Sin logos custom: el pdf_service usará los defaults muc/unemi/feue
    diseno.logo_header_1 = None
    diseno.logo_header_2 = None
    diseno.logo_header_3 = None
    # Limpiar firma 4 personalizada
    diseno.nombre_firma_4 = ''
    diseno.cargo_firma_4 = ''
    diseno.imagen_firma_4 = ''

    # Tomar las primeras 3 firmas institucionales activas (si existen)
    firmas = list(FirmaInstitucional.objects.filter(activa=True).order_by('orden', 'id')[:3])
    diseno.firma_inst_1 = firmas[0] if len(firmas) > 0 else None
    diseno.firma_inst_2 = firmas[1] if len(firmas) > 1 else None
    diseno.firma_inst_3 = firmas[2] if len(firmas) > 2 else None

    diseno.save()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_disenoglobal'),
    ]

    operations = [
        migrations.AddField(
            model_name='lotecertificados',
            name='personalizar_diseno',
            field=models.BooleanField(
                default=False,
                help_text='Si está activo, este lote usará su propio diseño en lugar del Diseño Global.',
                verbose_name='Personalizar diseño para este lote',
            ),
        ),
        migrations.RunPython(reset_diseno_global, reverse_noop),
    ]
