# Fases 5-7: API REST con Django REST Framework

## Objetivo

Crear una API REST paralela al panel admin web que pueda ser consumida por:
- La app Expo/React Native (futuro)
- Integraciones externas (otras universidades, sistemas legacy)
- Automatizaciones y scripts

**El admin panel web sigue siendo Django MVC**, no se toca. La API es capa adicional.

---

## Fase 5: Setup DRF + Auth JWT (1 dia)

### Objetivos
- Instalar y configurar Django REST Framework
- Implementar autenticacion JWT (para movil)
- Mantener sesiones para admin web
- Configurar versionado de API

### Dependencias a agregar

```txt
# requirements.txt
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
drf-spectacular==0.27.2      # OpenAPI/Swagger docs
django-filter==24.3
django-cors-headers==4.4.0
```

### Configuracion `config/settings/base.py`

```python
INSTALLED_APPS = [
    # ... existentes ...
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
    'api',  # nuestra nueva app
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # arriba de todo
    # ... resto ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # para admin web tambien
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',      # busquedas publicas
        'user': '1000/hour',     # usuarios autenticados
    },
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Certify API',
    'DESCRIPTION': 'API para sistema de certificados UNEMI/MUC',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

CORS_ALLOWED_ORIGINS = [
    # Para dev de Expo
    'http://localhost:8081',
    'http://localhost:19006',
    # Produccion
    'https://muc-academy.up.railway.app',
]
CORS_ALLOW_CREDENTIALS = True
```

### Estructura app `api/`

```python
# api/apps.py
from django.apps import AppConfig
class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
```

```python
# api/urls.py
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Auth
    path('v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/auth/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('v1/auth/', include('api.auth.urls')),

    # Recursos
    path('v1/participants/', include('api.participants.urls')),
    path('v1/certificates/', include('api.certificates.urls')),
    path('v1/sessions/', include('api.sessions.urls')),
    path('v1/batches/', include('api.batches.urls')),
    path('v1/recommendations/', include('api.recommendations.urls')),
    path('v1/ai/', include('api.ai.urls')),

    # Docs (publicos)
    path('v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
```

```python
# config/urls.py (agregar)
urlpatterns = [
    # ... existentes ...
    path('api/', include('api.urls')),
]
```

### Paginacion custom

```python
# api/common/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

### Entregable
- `pip install` y migracion de `token_blacklist`
- `/api/v1/docs/` muestra Swagger UI funcional
- Login con JWT funciona via Postman/curl:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@unemi.edu.ec", "password": "..."}'
```

---

## Fase 6: Endpoints principales (2-3 dias)

### Objetivo
Implementar los endpoints que consumira Expo en el futuro.

### 6.1 Participants API

```python
# api/participants/serializers.py
from rest_framework import serializers
from core.models import Participante, Certificado

class CertificadoMinSerializer(serializers.ModelSerializer):
    lote_nombre = serializers.CharField(source='lote.nombre_lote', read_only=True)
    class Meta:
        model = Certificado
        fields = ['id', 'hash_verificacion', 'curso', 'fecha_curso', 'horas', 'lote_nombre']

class ParticipanteSerializer(serializers.ModelSerializer):
    certificados = CertificadoMinSerializer(many=True, read_only=True)
    certificados_count = serializers.IntegerField(source='certificados.count', read_only=True)
    class Meta:
        model = Participante
        fields = ['id', 'cedula', 'nombres', 'apellidos', 'email', 'celular', 'es_lider', 'certificados', 'certificados_count']
```

```python
# api/participants/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Participante
from .serializers import ParticipanteSerializer
from api.common.permissions import IsAdminOrReadOwn

class ParticipanteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Participante.objects.all()
    serializer_class = ParticipanteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['cedula', 'email', 'nombres', 'apellidos']

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener el propio perfil segun email/cedula del token."""
        # logica de self-lookup
        pass

    @action(detail=True, methods=['get'])
    def certificates(self, request, pk=None):
        p = self.get_object()
        serializer = CertificadoMinSerializer(p.certificados.all(), many=True)
        return Response(serializer.data)
```

```python
# api/participants/urls.py
from rest_framework.routers import DefaultRouter
from .views import ParticipanteViewSet

router = DefaultRouter()
router.register('', ParticipanteViewSet, basename='participants')
urlpatterns = router.urls
```

### 6.2 Certificates API

Endpoints:
- `GET /api/v1/certificates/?q=search` — busqueda publica
- `GET /api/v1/certificates/{hash}/` — detalle
- `GET /api/v1/certificates/{hash}/download/` — devuelve PDF o URL firmada
- `GET /api/v1/certificates/{hash}/verify/` — valida autenticidad (publico)

### 6.3 Sessions API

Endpoints:
- `GET /api/v1/sessions/upcoming/` — proximas sesiones
- `GET /api/v1/sessions/{id}/` — detalle
- `POST /api/v1/sessions/{id}/confirm/` — confirmar asistencia
- `POST /api/v1/sessions/{id}/checkin/` — marcar asistencia con QR

### 6.4 Batches API (admin only)

Endpoints:
- `GET /api/v1/batches/` — listar
- `POST /api/v1/batches/` — crear
- `POST /api/v1/batches/{id}/process_excel/` — procesar Excel

### 6.5 Permisos custom

```python
# api/common/permissions.py
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    """Participante solo puede ver sus propios datos."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.email.lower() == request.user.email.lower()
```

### Entregable
- 15+ endpoints documentados en Swagger
- Coleccion Postman exportada (para Expo dev)
- Commit: `feat: implement core REST API endpoints with DRF`

---

## Fase 7: Endpoints de IA (1 dia)

### Objetivo
Exponer los servicios de IA como endpoints consumibles.

### Endpoints

```
POST /api/v1/ai/copilot/body          # Generar cuerpo certificado
POST /api/v1/ai/excel/map-columns     # Mapeo inteligente de Excel
POST /api/v1/ai/voice/extract         # Extraer entidades de voz transcrita
GET  /api/v1/ai/insights/dashboard    # Insights narrativos del dashboard
GET  /api/v1/ai/recommendations/{email}  # Eventos recomendados
```

Estos endpoints seran implementados completamente en las Fases 8-12. En esta fase solo se crea el scaffolding:

```python
# api/ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class CopilotBodyView(APIView):
    def post(self, request):
        # placeholder, se implementa en Fase 9
        return Response({'detail': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)

class ExcelMapColumnsView(APIView):
    def post(self, request):
        return Response({'detail': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)

# ... etc
```

```python
# api/ai/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('copilot/body/', views.CopilotBodyView.as_view()),
    path('excel/map-columns/', views.ExcelMapColumnsView.as_view()),
    path('voice/extract/', views.VoiceExtractView.as_view()),
    path('insights/dashboard/', views.InsightsDashboardView.as_view()),
    path('recommendations/<str:email>/', views.RecommendationsView.as_view()),
]
```

### Entregable
- Estructura completa pero placeholder
- Swagger muestra los endpoints con schemas tentativos
- Ready para implementacion en siguientes fases
