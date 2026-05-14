from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import AesculiaPasswordResetForm, AesculiaSetPasswordForm
from .views import AesculiaLoginView, AesculiaLogoutView

app_name = "auth"

urlpatterns = [
    path("login/", AesculiaLoginView.as_view(), name="login"),
    path(
        "logout/",
        AesculiaLogoutView.as_view(next_page=reverse_lazy("landing")),
        name="logout",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            form_class=AesculiaPasswordResetForm,
            template_name="auth/password_reset.html",
            email_template_name="auth/emails/password_reset_email.txt",
            subject_template_name="auth/emails/password_reset_subject.txt",
            success_url=reverse_lazy("auth:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=AesculiaSetPasswordForm,
            template_name="auth/password_reset_confirm.html",
            success_url=reverse_lazy("auth:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
