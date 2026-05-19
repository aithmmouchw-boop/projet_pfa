from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import AesculiaLoginForm, AesculiaSignupForm

ROLE_REDIRECTS = {
    "patient":   reverse_lazy("patients:patient_dashboard"),
    "medecin":   reverse_lazy("medecins:medecin_dashboard"),
    "infirmier": reverse_lazy("secretaire:secretaire_dashboard"),
    "caissier":  reverse_lazy("facturation:caissier_dashboard"),
}


def success_url_for_user(user):
    if user.is_superuser or (getattr(user, "role", None) == "admin" and user.is_staff):
        return str(reverse_lazy("admin:index"))
    role = getattr(user, "role", None) or "patient"
    url = ROLE_REDIRECTS.get(role)
    return str(url) if url else str(reverse_lazy("patients:patient_dashboard"))


class AesculiaLogoutView(LogoutView):
    """Compatible Django 5 — fonctionne en GET et POST."""
    http_method_names = ["get", "post", "head", "options", "trace"]
    next_page = reverse_lazy("landing")

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(self.next_page)


class AesculiaLoginView(LoginView):
    """Connexion unique — redirection selon le rôle."""
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
        return success_url_for_user(self.request.user)


class AesculiaSignupView(FormView):
    """Inscription avec choix du role et creation du profil necessaire."""

    template_name = "auth/register.html"
    form_class = AesculiaSignupForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(success_url_for_user(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(
            self.request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        messages.success(self.request, "Votre compte a ete cree avec succes.")
        return redirect(success_url_for_user(user))
