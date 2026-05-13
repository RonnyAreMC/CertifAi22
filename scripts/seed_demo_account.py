"""Seed datos demo para la cuenta de tesis (test@unemi.edu.ec).

Uso:
    python manage.py shell < scripts/seed_demo_account.py
"""
from datetime import date, time, timedelta

from django.utils import timezone

from core.models import (
    Certificado, ConfirmacionAsistencia, LoteCertificados, Participante,
    SesionAsistencia,
)

EMAIL = "test@unemi.edu.ec"
p = Participante.objects.get(email=EMAIL)
print(f"Participante: {p.id} {p.nombre_completo}")

# ── Lote + 3 certificados ────────────────────────────────────────
lote, _ = LoteCertificados.objects.get_or_create(
    nombre_lote="Seminario Demo Tesis 2026",
)
cursos = [
    ("Introducción a la Inteligencia Artificial", date(2026, 3, 15), 12),
    ("Bases de Datos para Investigación",        date(2026, 3, 22), 8),
    ("Fundamentos de UX en Aplicaciones Móviles", date(2026, 4, 5),  6),
]
for curso, fecha, horas in cursos:
    Certificado.objects.get_or_create(
        lote=lote,
        cedula=p.cedula or "0000000000",
        email=p.email,
        curso=curso,
        defaults={
            "participante": p,
            "nombres": p.nombres,
            "apellidos": p.apellidos,
            "fecha_curso": fecha,
            "horas": horas,
        },
    )
print(f"Certificados de {EMAIL}: {Certificado.objects.filter(email=EMAIL).count()}")

# ── 2 eventos próximos (1 inscrito, 1 disponible) ────────────────
hoy = timezone.localdate()
ev_inscrito, _ = SesionAsistencia.objects.get_or_create(
    titulo="Webinar · Tendencias de IA en Educación",
    defaults={
        "lote": lote,
        "descripcion": "Sesión virtual con expertos en aplicaciones de IA en aulas universitarias.",
        "modalidad": "virtual",
        "plataforma_virtual": "google_meet",
        "enlace_virtual": "https://meet.google.com/abc-defg-hij",
        "fecha": hoy + timedelta(days=3),
        "hora_inicio": time(18, 0),
        "hora_fin": time(20, 0),
    },
)
ConfirmacionAsistencia.objects.get_or_create(participante=p, sesion=ev_inscrito)

ev_disponible, _ = SesionAsistencia.objects.get_or_create(
    titulo="Taller · Diseño de Tesis con Métodos Mixtos",
    defaults={
        "lote": lote,
        "descripcion": "Taller presencial en Auditorio FACS UNEMI. Cupos limitados.",
        "modalidad": "presencial",
        "lugar": "Auditorio FACS · Bloque B",
        "fecha": hoy + timedelta(days=10),
        "hora_inicio": time(9, 0),
        "hora_fin": time(12, 0),
    },
)
print(f"Eventos: inscrito={ev_inscrito.id} disponible={ev_disponible.id}")
print("Demo seed OK ✓")
