from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from .forms import CreaUtenteCliente, CreaUtenteGestoreFilm, CreaUtenteSegretario


def home_view(request):
    return render(request, "home.html")

def info_view(request):
    return render(request, "info.html")


class UserCreateView(CreateView):
    form_class = CreaUtenteCliente
    template_name = "user_create.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Utente creato correttamente, ora puoi accedere.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Ci sono errori nel form, controlla i campi evidenziati.")
        return super().form_invalid(form)
    
