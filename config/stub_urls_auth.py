"""Vues factices pour que {% url 'auth:login' %} fonctionne en démo."""

from django.http import HttpResponse
from django.urls import path

app_name = "auth"


def login_stub(request):
    return HttpResponse(
        "<h1>Démo</h1><p>Branchez ici votre vraie page de connexion staff "
        "(<code>auth:login</code>).</p>",
        content_type="text/html; charset=utf-8",
    )


urlpatterns = [
    path("connexion/", login_stub, name="login"),
]
