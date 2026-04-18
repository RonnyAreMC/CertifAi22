from django.urls import path
from . import views

urlpatterns = [
    path('copilot/body/', views.CopilotBodyView.as_view(), name='ai_copilot_body'),
    path('excel/map-columns/', views.ExcelMapColumnsView.as_view(), name='ai_excel_map'),
    path('voice/extract/', views.VoiceExtractView.as_view(), name='ai_voice_extract'),
    path('insights/dashboard/', views.InsightsDashboardView.as_view(), name='ai_insights_dashboard'),
    path('recommendations/<str:email>/', views.RecommendationsView.as_view(), name='ai_recommendations'),
]
