from django.urls import path

from . import views

app_name = "secretaire"

urlpatterns = [
    path("dashboard/", views.SecretaireDashboardView.as_view(), name="secretaire_dashboard"),
    path("rdv/<int:pk>/arriver/", views.RdvMarquerArriveView.as_view(), name="rdv_arriver"),
    path("rdv/<int:pk>/constantes/", views.RdvConstantesView.as_view(), name="rdv_constantes"),
]
