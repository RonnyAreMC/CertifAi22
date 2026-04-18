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
