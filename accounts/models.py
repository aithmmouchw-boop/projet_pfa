from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("L’adresse e-mail est obligatoire."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Le superuser doit avoir is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Le superuser doit avoir is_superuser=True."))
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Utilisateur plateforme — connexion par e-mail et rôle pour la redirection."""

    username = None
    # 191 : index unique compatible utf8mb4 (limite de longueur de clé MySQL / InnoDB).
    email = models.EmailField(_("adresse e-mail"), unique=True, max_length=191)
    role = models.CharField(
        max_length=20,
        choices=[
            ("patient", _("Patient")),
            ("medecin", _("Médecin")),
            ("infirmier", _("Secretaire")),
            ("caissier", _("Caissier")),
            ("admin", _("Administrateur")),
        ],
        default="patient",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")

    def __str__(self) -> str:
        return self.email


class InfirmierAccount(User):
    class Meta:
        proxy = True
        verbose_name = _("secretaire")
        verbose_name_plural = _("secretaires")


class CaissierAccount(User):
    class Meta:
        proxy = True
        verbose_name = _("caissier")
        verbose_name_plural = _("caissiers")
