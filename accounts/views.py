from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .forms import AesculiaLoginForm


class AesculiaLogoutView(LogoutView):
    """Permet la déconnexion par lien (GET) — pratique sur la vitrine ; en production préférer POST."""

    http_method_names = ["get", "post", "head", "options", "trace"]


ROLE_REDIRECTS = {
    "patient": reverse_lazy("patient_dashboard"),
    "medecin": reverse_lazy("medecin_dashboard"),
    "infirmier": reverse_lazy("infirmier_dashboard"),
    "caissier": reverse_lazy("caissier_dashboard"),
}


class AesculiaLoginView(LoginView):
    """Connexion unique — redirection selon le rôle (ou admin Django si superuser)."""

    template_name = "auth/login.html"
    authentication_form = AesculiaLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember = self.request.POST.get("remember")
        if remember:
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return str(reverse_lazy("admin:index"))
        role = getattr(user, "role", None) or "patient"
        if role == "admin" and user.is_staff:
            return str(reverse_lazy("admin:index"))
        url = ROLE_REDIRECTS.get(role)
        if url is not None:
            return str(url)
        return str(reverse_lazy("patient_dashboard"))
