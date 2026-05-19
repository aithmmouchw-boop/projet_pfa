from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import User
from consultations.models import DossierPatient
from .models import Patient
from .utils import generer_num_dossier


class PatientAdminForm(forms.ModelForm):
    email = forms.EmailField(label="Adresse e-mail")
    first_name = forms.CharField(label="Prenom", max_length=150, required=False)
    last_name = forms.CharField(label="Nom", max_length=150, required=False)
    password = forms.CharField(
        label="Mot de passe",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Obligatoire a la creation. Laissez vide pour garder le mot de passe actuel.",
    )
    is_active = forms.BooleanField(label="Compte actif", required=False, initial=True)

    class Meta:
        model = Patient
        fields = ("num_dossier", "date_naissance", "telephone", "adresse")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["num_dossier"].required = False
        self.fields["num_dossier"].help_text = "Laissez vide pour generer un numero automatiquement."
        if self.instance.pk and self.instance.user_id:
            user = self.instance.user
            self.fields["email"].initial = user.email
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["is_active"].initial = user.is_active
        else:
            self.fields["password"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("Un compte existe deja avec cet e-mail.")
        return email


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    form = PatientAdminForm
    list_display = (
        "num_dossier",
        "nom_complet",
        "account_email",
        "telephone",
        "date_naissance",
        "rdv_total",
    )
    list_filter = ("date_naissance",)
    search_fields = (
        "num_dossier",
        "user__email",
        "user__first_name",
        "user__last_name",
        "telephone",
    )
    readonly_fields = (
        "dossier_link",
        "rdv_total",
        "consultations_total",
        "factures_total",
    )
    fieldsets = (
        (
            "Compte patient",
            {"fields": ("email", "first_name", "last_name", "password", "is_active")},
        ),
        (
            "Profil patient",
            {"fields": ("num_dossier", "date_naissance", "telephone", "adresse")},
        ),
        (
            "Liaisons",
            {"fields": ("dossier_link", "rdv_total", "consultations_total", "factures_total")},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    @admin.display(description="Nom")
    def nom_complet(self, obj):
        return obj.user.get_full_name() or obj.user.email

    @admin.display(description="E-mail")
    def account_email(self, obj):
        return obj.user.email

    @admin.display(description="Dossier medical")
    def dossier_link(self, obj):
        if not obj.pk:
            return "-"
        dossier = DossierPatient.objects.filter(patient=obj).first()
        if not dossier:
            return "Aucun dossier"
        url = reverse("admin:consultations_dossierpatient_change", args=[dossier.pk])
        return format_html('<a href="{}">{}</a>', url, dossier.num_dossier)

    @admin.display(description="Rendez-vous")
    def rdv_total(self, obj):
        if not obj.pk:
            return 0
        return obj.rendez_vous.count()

    @admin.display(description="Consultations")
    def consultations_total(self, obj):
        if not obj.pk:
            return 0
        return obj.consultations.count()

    @admin.display(description="Factures")
    def factures_total(self, obj):
        if not obj.pk:
            return 0
        return obj.factures.count()

    def save_model(self, request, obj, form, change):
        user = obj.user if obj.pk and obj.user_id else User(role="patient")
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data["first_name"].strip()
        user.last_name = form.cleaned_data["last_name"].strip()
        user.role = "patient"
        user.is_staff = False
        user.is_superuser = False
        user.is_active = form.cleaned_data["is_active"]
        if form.cleaned_data["password"]:
            user.set_password(form.cleaned_data["password"])
        user.save()
        obj.user = user
        if not obj.num_dossier:
            obj.num_dossier = generer_num_dossier()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        user = obj.user
        super().delete_model(request, obj)
        user.delete()

    def delete_queryset(self, request, queryset):
        user_ids = list(queryset.values_list("user_id", flat=True))
        super().delete_queryset(request, queryset)
        User.objects.filter(pk__in=user_ids).delete()
