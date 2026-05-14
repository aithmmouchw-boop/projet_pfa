from django.urls import path

from .views import BookingCreateView, BookingDoneView

app_name = "appointments"

urlpatterns = [
    path("nouveau/", BookingCreateView.as_view(), name="create"),
    path("nouveau/merci/", BookingDoneView.as_view(), name="create_done"),
]
