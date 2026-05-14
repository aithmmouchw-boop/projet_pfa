from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import AppointmentRequestForm


class BookingCreateView(FormView):
    """Demande de RDV — enregistrée pour le concierge (patient connecté ou invité)."""

    form_class = AppointmentRequestForm
    template_name = "appointments/create.html"
    success_url = reverse_lazy("appointments:create_done")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user if self.request.user.is_authenticated else None
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        q = self.request.GET
        initial["doctor_ref"] = q.get("doctor", "").strip()[:200]
        initial["service_ref"] = q.get("service", "").strip()[:200]
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET
        ctx["prefill_doctor"] = q.get("doctor", "").strip()
        ctx["prefill_service"] = q.get("service", "").strip()
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.request.user.is_authenticated:
            obj.user = self.request.user
        obj.save()
        messages.success(
            self.request,
            "Votre demande a bien été enregistrée. Nous vous recontactons sous 24h ouvrées.",
        )
        return super().form_valid(form)


class BookingDoneView(TemplateView):
    """Confirmation après envoi d'une demande de rendez-vous."""

    template_name = "appointments/create_done.html"
