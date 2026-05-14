from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("sitepages.urls")),
    path("appointments/", include(("appointments.urls", "appointments"))),
    path("auth/", include("accounts.urls")),
]
