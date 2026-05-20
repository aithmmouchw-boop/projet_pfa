from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("complet/", views.PatientOnboardingView.as_view(), name="onboarding"),
    path("dashboard/", views.PatientDashboardView.as_view(), name="patient_dashboard"),
    path("rdv/", views.RdvListView.as_view(), name="rdv_list"),
    path("rdv/nouveau/", views.RdvBookingView.as_view(), name="rdv_nouveau"),
    path("rdv/<int:pk>/merci/", views.RdvSuccessView.as_view(), name="rdv_success"),
    path("rdv/<int:pk>/annuler/", views.RdvAnnulerView.as_view(), name="rdv_annuler"),
    path("dossier/", views.DossierView.as_view(), name="dossier"),
    path("factures/", views.FacturesListView.as_view(), name="factures"),
    path("factures/<int:pk>/", views.PatientFactureDetailView.as_view(), name="facture_detail"),
]
