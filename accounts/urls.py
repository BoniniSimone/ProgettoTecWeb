from django.urls import path
from django.contrib.auth.views import LoginView
from .forms import BootstrapAuthenticationForm
from .views import mie_prenotazioni, prenotazioni_utente, register, UserDeleteView, UserListView, ToggleSocioView


app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", LoginView.as_view(authentication_form=BootstrapAuthenticationForm), name="login"),
    path("prenotazioni/", mie_prenotazioni, name="mie_prenotazioni"),
    path("utenti/", UserListView.as_view(), name="user_list"),
    path("utenti/<int:user_id>/elimina/", UserDeleteView.as_view(), name="user_delete"),
    path("utenti/<int:user_id>/socio/", ToggleSocioView.as_view(), name="user_toggle_socio"),
    path("utenti/<int:user_id>/prenotazioni/", prenotazioni_utente, name="user_prenotazioni"),

]
