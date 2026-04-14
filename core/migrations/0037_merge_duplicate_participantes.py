# Data migration: merge duplicate Participante records before adding unique constraint
from django.db import migrations


def merge_duplicates(apps, schema_editor):
    """
    Merge duplicate Participante records by email and by cedula.
    Keeps the oldest record (first created) as canonical, moves all
    related objects (certificados, confirmaciones, registros) to it,
    then deletes the duplicates.
    """
    Participante = apps.get_model('core', 'Participante')
    Certificado = apps.get_model('core', 'Certificado')
    ConfirmacionAsistencia = apps.get_model('core', 'ConfirmacionAsistencia')
    RegistroAsistencia = apps.get_model('core', 'RegistroAsistencia')

    from django.db.models import Count, Min
    from django.db.models.functions import Lower

    merged_count = 0

    # --- Pass 1: merge by email (case-insensitive) ---
    dupes_email = (
        Participante.objects.exclude(email='')
        .annotate(email_lower=Lower('email'))
        .values('email_lower')
        .annotate(cnt=Count('id'), first_id=Min('id'))
        .filter(cnt__gt=1)
    )

    for group in dupes_email:
        canonical_id = group['first_id']
        canonical = Participante.objects.get(id=canonical_id)
        duplicates = (
            Participante.objects.filter(email__iexact=group['email_lower'])
            .exclude(id=canonical_id)
        )

        for dup in duplicates:
            # Enrich canonical with data it might be missing
            if dup.cedula and not canonical.cedula:
                canonical.cedula = dup.cedula
            if dup.celular and not canonical.celular:
                canonical.celular = dup.celular
            if dup.es_lider and not canonical.es_lider:
                canonical.es_lider = True

            # Move related objects
            Certificado.objects.filter(participante=dup).update(participante=canonical)
            ConfirmacionAsistencia.objects.filter(participante=dup).update(participante=canonical)
            RegistroAsistencia.objects.filter(participante=dup).update(participante=canonical)

            dup.delete()
            merged_count += 1

        canonical.save()

    # --- Pass 2: merge by cedula (for cases where email differs) ---
    dupes_cedula = (
        Participante.objects.exclude(cedula='')
        .values('cedula')
        .annotate(cnt=Count('id'), first_id=Min('id'))
        .filter(cnt__gt=1)
    )

    for group in dupes_cedula:
        canonical_id = group['first_id']
        canonical = Participante.objects.get(id=canonical_id)
        duplicates = (
            Participante.objects.filter(cedula=group['cedula'])
            .exclude(id=canonical_id)
        )

        for dup in duplicates:
            if dup.email and not canonical.email:
                canonical.email = dup.email
            if dup.celular and not canonical.celular:
                canonical.celular = dup.celular
            if dup.es_lider and not canonical.es_lider:
                canonical.es_lider = True

            Certificado.objects.filter(participante=dup).update(participante=canonical)
            ConfirmacionAsistencia.objects.filter(participante=dup).update(participante=canonical)
            RegistroAsistencia.objects.filter(participante=dup).update(participante=canonical)

            dup.delete()
            merged_count += 1

        canonical.save()

    # --- Pass 3: link orphaned Certificados (participante=NULL) ---
    orphans = Certificado.objects.filter(participante__isnull=True)
    linked_count = 0

    for cert in orphans:
        cedula = cert.cedula.strip()
        email = cert.email.strip().lower() if cert.email else ''
        is_generated = cedula.startswith('GEN-') or not cedula
        real_cedula = '' if is_generated else cedula

        participante = None
        if real_cedula:
            participante = Participante.objects.filter(cedula=real_cedula).first()
        if not participante and email:
            participante = Participante.objects.filter(email__iexact=email).first()

        if participante:
            cert.participante = participante
            cert.save(update_fields=['participante'])
            linked_count += 1
        else:
            # Create new Participante for truly orphaned cert
            participante = Participante.objects.create(
                cedula=real_cedula,
                nombres=cert.nombres or '',
                apellidos=cert.apellidos or '',
                email=email,
                celular=cert.celular or '',
            )
            cert.participante = participante
            cert.save(update_fields=['participante'])
            linked_count += 1

    if merged_count or linked_count:
        print(f'  Merged {merged_count} duplicate participantes, linked {linked_count} orphaned certificates.')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_add_per_signature_position'),
    ]

    operations = [
        migrations.RunPython(merge_duplicates, migrations.RunPython.noop),
    ]
