from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path("prenota/<int:proiezione_id>/", views.prenota, name="prenota"),
    path("prenotazioni/<int:biglietto_id>/annulla/", views.annulla_biglietto, name="annulla_biglietto"),
    path("film/<int:film_id>/prenotazioni/", views.PrenotazioniFilmView.as_view(), name="prenotazioni_film"),
    path("biglietti/<int:biglietto_id>/annulla-staff/", views.BigliettoStaffDeleteView.as_view(), name="annulla_biglietto_staff"),
]
