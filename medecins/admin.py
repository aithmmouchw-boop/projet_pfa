from django import forms
from django.contrib import admin

from clinic_common.clinical_specialties import SPECIALTY_CHOICES
from accounts.models import User
from .models import Medecin


class MedecinAdminForm(forms.ModelForm):
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
        model = Medecin
        fields = ("specialite", "tarif_consultation", "bio", "photo", "actif")
        widgets = {
            "specialite": forms.Select(choices=SPECIALTY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = list(SPECIALTY_CHOICES)
        if self.instance.pk and self.instance.specialite:
            values = {value for value, _label in choices}
            if self.instance.specialite not in values:
                choices.insert(0, (self.instance.specialite, self.instance.specialite))
        self.fields["specialite"].widget.choices = choices
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


@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    form = MedecinAdminForm
    list_display = (
        "nom_complet",
        "account_email",
        "specialite",
        "tarif_consultation",
        "actif",
        "rdv_total",
    )
    list_filter = ("actif", "specialite")
    search_fields = ("user__email", "user__first_name", "user__last_name", "specialite")
    readonly_fields = ("rdv_total", "consultations_total")
    fieldsets = (
        (
            "Compte medecin",
            {"fields": ("email", "first_name", "last_name", "password", "is_active")},
        ),
        (
            "Profil medecin",
            {"fields": ("specialite", "tarif_consultation", "bio", "photo", "actif")},
        ),
        ("Liaisons", {"fields": ("rdv_total", "consultations_total")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    @admin.display(description="Nom")
    def nom_complet(self, obj):
        return obj.user.get_full_name() or obj.user.email

    @admin.display(description="E-mail")
    def account_email(self, obj):
        return obj.user.email

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

    def save_model(self, request, obj, form, change):
        user = obj.user if obj.pk and obj.user_id else User(role="medecin")
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data["first_name"].strip()
        user.last_name = form.cleaned_data["last_name"].strip()
        user.role = "medecin"
        user.is_staff = False
        user.is_superuser = False
        user.is_active = form.cleaned_data["is_active"]
        if form.cleaned_data["password"]:
            user.set_password(form.cleaned_data["password"])
        user.save()
        obj.user = user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        user = obj.user
        super().delete_model(request, obj)
        user.delete()

    def delete_queryset(self, request, queryset):
        user_ids = list(queryset.values_list("user_id", flat=True))
        super().delete_queryset(request, queryset)
        User.objects.filter(pk__in=user_ids).delete()
