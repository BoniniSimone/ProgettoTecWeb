from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.contrib import messages
from .forms import CreaUtenteCliente, CreaUtenteGestoreFilm, CreaUtenteSegretario
from accounts.models import NewsletterSubscription
from accounts.forms import NewsletterSubscribeForm

class InfoView(FormView):
    template_name = "info.html"
    form_class = NewsletterSubscribeForm
    success_url = reverse_lazy("info")  # ricarica la pagina

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        _, created = NewsletterSubscription.objects.get_or_create(email=email)

        # passiamo un esito al template (senza usare messages, se vuoi minimal)
        self.request.session["newsletter_esito"] = "ok" if created else "exists"
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["newsletter_esito"] = "invalid"
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["newsletter_esito"] = self.request.session.pop("newsletter_esito", None)
        return ctx

def home_view(request):
    return render(request, "home.html")


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
    
