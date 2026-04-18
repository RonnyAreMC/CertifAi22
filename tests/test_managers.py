"""Tests de QuerySets y Managers custom."""
import pytest

from tests.factories import CertificadoFactory, ParticipanteFactory, SesionFactory


@pytest.mark.django_db
class TestCertificadoManager:
    def test_search_by_cedula(self):
        c1 = CertificadoFactory(cedula='0912345678')
        CertificadoFactory(cedula='0999999999')
        from core.models import Certificado
        results = Certificado.objects.search('0912')
        assert c1 in results
        assert results.count() == 1

    def test_search_empty_returns_none(self):
        CertificadoFactory()
        from core.models import Certificado
        assert Certificado.objects.search('').count() == 0

    def test_downloaded_filters_by_count(self):
        CertificadoFactory(descargas_count=0)
        CertificadoFactory(descargas_count=5)
        from core.models import Certificado
        assert Certificado.objects.downloaded().count() == 1

    def test_with_relations_prefetches(self, django_assert_max_num_queries):
        CertificadoFactory()
        from core.models import Certificado
        with django_assert_max_num_queries(2):
            list(Certificado.objects.with_relations())

    def test_search_multi_token_is_AND_not_OR(self):
        """'Adriana Carolina' NO debe matchear a 'Jacqueline Gonzalez' ni a 'Adriana Smith'."""
        from core.models import Certificado
        # Match exacto (ambas palabras)
        match = CertificadoFactory(nombres='ADRIANA CAROLINA', apellidos='CORTEZ')
        # Solo una palabra
        only_adriana = CertificadoFactory(nombres='ADRIANA', apellidos='VILLACRES')
        only_carolina = CertificadoFactory(nombres='CAROLINA', apellidos='LUCAS')
        # Ninguna palabra
        CertificadoFactory(nombres='JACQUELINE', apellidos='GONZALEZ')

        results = list(Certificado.objects.search('Adriana Carolina'))
        assert match in results
        assert only_adriana not in results
        assert only_carolina not in results
        assert len(results) == 1

    def test_search_dedupes_by_person_course(self):
        """Dos certificados del mismo (cedula, curso) → solo uno aparece tras dedupe."""
        from core.models import Certificado
        CertificadoFactory(cedula='0912345678', curso='MATH', nombres='A')
        dup = CertificadoFactory(cedula='0912345678', curso='MATH', nombres='A')
        different = CertificadoFactory(cedula='0912345678', curso='FISICA', nombres='A')
        ids = set(Certificado.objects.deduped_by_person_course().values_list('id', flat=True))
        assert dup.id in ids  # el más reciente (mayor id) queda
        assert different.id in ids  # distinto curso queda
        assert len(ids) == 2


@pytest.mark.django_db
class TestParticipanteManager:
    def test_search_name_tokens(self):
        ParticipanteFactory(nombres='Ana', apellidos='García')
        ParticipanteFactory(nombres='Juan', apellidos='Pérez')
        from core.models import Participante
        results = Participante.objects.search('Ana')
        assert results.count() == 1

    def test_lideres_filter(self):
        ParticipanteFactory(es_lider=False)
        ParticipanteFactory(es_lider=True)
        from core.models import Participante
        assert Participante.objects.lideres().count() == 1


@pytest.mark.django_db
class TestSesionManager:
    def test_upcoming_excludes_past(self):
        from datetime import date, timedelta
        SesionFactory(fecha=date.today() - timedelta(days=1))  # past
        future = SesionFactory(fecha=date.today() + timedelta(days=1))
        from core.models import SesionAsistencia
        upcoming = SesionAsistencia.objects.upcoming()
        assert future in upcoming
        assert upcoming.count() == 1

    def test_past_reverse(self):
        from datetime import date, timedelta
        past = SesionFactory(fecha=date.today() - timedelta(days=5))
        SesionFactory(fecha=date.today() + timedelta(days=3))
        from core.models import SesionAsistencia
        assert past in SesionAsistencia.objects.past()
