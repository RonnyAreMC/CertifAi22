# Generated manually 2026-04-17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_unique_email_participante'),
    ]

    operations = [
        migrations.AddField(
            model_name='sesionasistencia',
            name='imagen_banner',
            field=models.ImageField(
                blank=True, null=True,
                upload_to='sesiones_banners/',
                verbose_name='Imagen de banner',
                help_text='Imagen promocional que se muestra en la página de registro',
            ),
        ),
        migrations.AddField(
            model_name='sesionasistencia',
            name='modalidad',
            field=models.CharField(
                choices=[('presencial', 'Presencial'), ('virtual', 'Virtual')],
                default='presencial',
                max_length=15,
                verbose_name='Modalidad',
            ),
        ),
        migrations.AddField(
            model_name='sesionasistencia',
            name='plataforma_virtual',
            field=models.CharField(
                blank=True, default='',
                choices=[
                    ('zoom', 'Zoom'),
                    ('meet', 'Google Meet'),
                    ('teams', 'Microsoft Teams'),
                    ('otro', 'Otra plataforma'),
                ],
                max_length=15,
                verbose_name='Plataforma',
                help_text='Solo aplica si la modalidad es virtual',
            ),
        ),
        migrations.AddField(
            model_name='sesionasistencia',
            name='enlace_virtual',
            field=models.URLField(
                blank=True, default='', max_length=500,
                verbose_name='Enlace de reunión',
                help_text='URL de Zoom/Meet/Teams u otra plataforma (solo si es virtual)',
            ),
        ),
    ]
