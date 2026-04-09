from django.db import migrations, models
import django.db.models.deletion


def seed_diseno_global(apps, schema_editor):
    """Crea el singleton inicial copiando del primer lote si existe."""
    DisenoGlobal = apps.get_model('core', 'DisenoGlobal')
    LoteCertificados = apps.get_model('core', 'LoteCertificados')

    if DisenoGlobal.objects.filter(pk=1).exists():
        return

    primer_lote = LoteCertificados.objects.order_by('id').first()
    if primer_lote:
        DisenoGlobal.objects.create(
            pk=1,
            plantilla=primer_lote.plantilla or 'clasico',
            color_primario=primer_lote.color_primario or '#162054',
            color_secundario=primer_lote.color_secundario or '#D4AF37',
            color_terciario=primer_lote.color_terciario or '#F3F4F6',
            color_texto=primer_lote.color_texto or '#333333',
            cuerpo_certificado=primer_lote.cuerpo_certificado or '',
            firma_inst_1=primer_lote.firma_inst_1,
            firma_inst_2=primer_lote.firma_inst_2,
            firma_inst_3=primer_lote.firma_inst_3,
            nombre_firma_4=primer_lote.nombre_firma_4 or '',
            cargo_firma_4=primer_lote.cargo_firma_4 or '',
            imagen_firma_4=primer_lote.imagen_firma_4 or '',
            logo_header_1=primer_lote.logo_header_1,
            logo_header_2=primer_lote.logo_header_2,
            logo_header_3=primer_lote.logo_header_3,
        )
    else:
        DisenoGlobal.objects.create(pk=1)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_alter_lotecertificados_cuerpo_certificado'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisenoGlobal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plantilla', models.CharField(choices=[('clasico', 'Clásico (Elegante)'), ('moderno', 'Moderno (Barra Lateral)'), ('geometrico', 'Geométrico (Formas)')], default='clasico', max_length=20)),
                ('color_primario', models.CharField(default='#162054', max_length=7)),
                ('color_secundario', models.CharField(default='#D4AF37', max_length=7)),
                ('color_terciario', models.CharField(default='#F3F4F6', max_length=7)),
                ('color_texto', models.CharField(default='#333333', max_length=7)),
                ('cuerpo_certificado', models.TextField(default="Por haber completado satisfactoriamente el curso de capacitación continua, demostrando compromiso y excelencia académica. Por su participación en el seminario '{curso}', contribuyendo de manera activa y profesional al desarrollo de nuevas competencias.")),
                ('nombre_firma_4', models.CharField(blank=True, default='', max_length=100)),
                ('cargo_firma_4', models.CharField(blank=True, default='', max_length=100)),
                ('imagen_firma_4', models.TextField(blank=True, default='')),
                ('logo_header_1', models.ImageField(blank=True, null=True, upload_to='logos/')),
                ('logo_header_2', models.ImageField(blank=True, null=True, upload_to='logos/')),
                ('logo_header_3', models.ImageField(blank=True, null=True, upload_to='logos/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('firma_inst_1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diseno_firma1', to='core.firmainstitucional')),
                ('firma_inst_2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diseno_firma2', to='core.firmainstitucional')),
                ('firma_inst_3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diseno_firma3', to='core.firmainstitucional')),
            ],
            options={
                'verbose_name': 'Diseño Global',
                'verbose_name_plural': 'Diseño Global',
            },
        ),
        migrations.RunPython(seed_diseno_global, reverse_noop),
    ]
