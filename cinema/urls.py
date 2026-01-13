from django.urls import path
from . import views
from .views import FilmInProgrammazioneListView

app_name = 'cinema'

urlpatterns = [
    path("programmazione/", FilmInProgrammazioneListView.as_view(), name="programmazione"),
    path("rassegna/", views.RassegnaFilmListView.as_view(), name="rassegna"),
    path("film/gestisci/", views.FilmListView.as_view(), name="film_gestisci"),
    path("prossimamente/", views.ProssimamenteFilmListView.as_view(), name="prossimamente"),
    path("recensioni/<int:pk>/elimina/", views.RecensioneDeleteView.as_view(), name="recensione_elimina"),


    path("film/crea/", views.FilmCreateView.as_view(), name="film_crea"),
    path("film/<int:pk>/", views.FilmDetailView.as_view(), name="film_detail"),
    path("film/<int:pk>/modifica/", views.FilmUpdateView.as_view(), name="film_modifica"),
    path("film/<int:pk>/elimina/", views.FilmDeleteView.as_view(), name="film_elimina"),

    path("proiezione/crea/<int:film_id>/", views.ProiezioneCreateView.as_view(), name="proiezione_crea"),
    path("proiezione/<int:pk>/modifica/", views.ProiezioneUpdateView.as_view(), name="proiezione_modifica"),
    path("proiezione/<int:pk>/elimina/", views.ProiezioneDeleteView.as_view(), name="proiezione_elimina"),

    path("api/sale/<int:sala_id>/impegni/", views.sala_impegni, name="sala_impegni"),
    path("ajax/film-suggestions/", views.film_suggestions, name="film_suggestions"),
    
]   