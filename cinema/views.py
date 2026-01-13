from django.db.models import Prefetch
from django.utils import timezone
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from braces.views import GroupRequiredMixin
from .models import Film, Proiezione, Recensione
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import ProiezioneForm, FilmForm, RecensioneForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from accounts.permissions import is_operational_staff
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

@require_GET
def sala_impegni(request, sala_id):
    now = timezone.now()
    qs = (
        Proiezione.objects
        .filter(sala_id=sala_id, data_ora__gte=now)
        .select_related("film")
        .order_by("data_ora")[:50] # limita a 50 righe
    )

    data = [
        {
            "data_ora": timezone.localtime(p.data_ora).strftime("%Y-%m-%d %H:%M"),
            "film": p.film.titolo,
        }
        for p in qs
    ]
    return JsonResponse({"impegni": data})


@require_GET
def film_suggestions(request):
    q = (request.GET.get("q") or "").strip() # legge il parametro 'q'
    if len(q) < 2:
        return JsonResponse({"results": []})

    qs = (
        Film.objects
        .filter(Q(titolo__icontains=q) | Q(regista__icontains=q))
        .order_by("titolo")
        .values("id", "titolo")[:5] #limito a 5 risultati
    )

    return JsonResponse({"results": list(qs)})



class FilmInProgrammazioneListView(ListView):
    model = Film
    template_name = "cinema/film_in_programmazione.html"
    context_object_name = "films"

    def get_queryset(self):
        now = timezone.now()

        proiezioni_future_qs = (
            Proiezione.objects
            .filter(data_ora__gte=now)
            .select_related("sala")
            .order_by("data_ora")
        )

        qs = (
            Film.objects
            # prendo solo film che hanno almeno una proiezione futura
            .filter(rassegna=False, proiezione__data_ora__gte=now, in_programmazione__lte=now)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "proiezione_set",
                    queryset=proiezioni_future_qs,
                    to_attr="proiezioni_future"
                )
            )
            .order_by("titolo")
        )
        return qs



class RassegnaFilmListView(ListView):
    model = Film
    template_name = "cinema/film_in_programmazione.html"
    context_object_name = "films"

    def get_queryset(self):
        now = timezone.now()

        proiezioni_future_qs = (
            Proiezione.objects
            .filter(data_ora__gte=now)
            .select_related("sala")
            .order_by("data_ora")
        )

        qs = (
            Film.objects
            # prendo solo film che hanno almeno una proiezione futura e che sono in rassegna
            .filter(rassegna=True, proiezione__data_ora__gte=now)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "proiezione_set",
                    queryset=proiezioni_future_qs,
                    to_attr="proiezioni_future"
                )
            )
            .order_by("titolo")
        )
        return qs



class FilmListView(ListView):
    model = Film
    template_name = "cinema/film_list.html"
    context_object_name = "films"

    def get_queryset(self):
        qs = super().get_queryset().order_by("titolo")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(titolo__icontains=q) |
                Q(regista__icontains=q)
            )
        return qs



class ProssimamenteFilmListView(ListView):
    model = Film
    template_name = "cinema/film_list.html"
    context_object_name = "films"

    def get_queryset(self):
        now = timezone.now()

        qs = (
            Film.objects
            # prendo solo film con data di uscita futura e non ancora in programmazione
            .filter(in_programmazione__gt=now, rassegna=False)
            .order_by("data_uscita")
        )
        return qs



class FilmCreateView(GroupRequiredMixin, CreateView):
    model = Film
    form_class = FilmForm
    template_name = "cinema/film_form.html"
    success_url = reverse_lazy("home")
    group_required = ["gestore_film"]
    superuser_allowed = True



class FilmDetailView(DetailView):
    model = Film
    template_name = "cinema/film_detail.html"
    context_object_name = "film"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proiezioni"] = (
            Proiezione.objects
            .filter(film=self.object, data_ora__gte=timezone.now())
            .select_related("sala")
            .order_by("data_ora")
        )
        context["today"] = timezone.now().date()
        context["recensioni"] = (
            Recensione.objects
            .filter(film=self.object)
            .select_related("autore")
            .order_by("-create_at", "-id")
        )
        context["recensione_form"] = kwargs.get("recensione_form") or RecensioneForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")

        form = RecensioneForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.film = self.object
            rec.autore = request.user
            rec.save()
            messages.success(request, "Recensione inserita con successo.")
            return redirect(f"{request.path}#recensioni")

        context = self.get_context_data(recensione_form=form)
        return self.render_to_response(context)



class RecensioneDeleteView(GroupRequiredMixin, View):
    group_required = ["gestore_film"]
    superuser_allowed = True

    def post(self, request, pk):
        recensione = get_object_or_404(Recensione, pk=pk)
        film_id = recensione.film_id
        recensione.delete()
        messages.success(request, "Recensione eliminata.")
        return redirect(reverse("cinema:film_detail", kwargs={"pk": film_id}) + "#recensioni")



class FilmUpdateView(GroupRequiredMixin, UpdateView):
    model = Film
    form_class = FilmForm
    template_name = "cinema/film_update.html"
    context_object_name = "film"
    success_url = reverse_lazy("home")
    group_required = ["gestore_film"]
    superuser_allowed = True
    raise_exception = True



class FilmDeleteView(GroupRequiredMixin, DeleteView):
    model = Film
    template_name = "cinema/film_delete.html"
    context_object_name = "film"
    success_url = reverse_lazy("home")
    group_required = ["gestore_film"]
    superuser_allowed = True
    raise_exception = True



class ProiezioneCreateView(GroupRequiredMixin, CreateView):
    model = Proiezione
    form_class = ProiezioneForm
    template_name = "cinema/proiezione_form.html"
    group_required = ["gestore_film"]
    superuser_allowed = True
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.film = Film.objects.get(pk=kwargs["film_id"])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["film"] = self.film
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["film"] = self.film
        context["proiezioni_film"] = (
            Proiezione.objects
            .filter(film=self.film, data_ora__gte=timezone.now())
            .select_related("sala")
            .order_by("data_ora")
        )
        context["title"] = "Aggiungi"
        return context

    def form_valid(self, form):
        form.instance.film = self.film
        messages.success(self.request, "Proiezione creata con successo.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("cinema:film_detail", kwargs={"pk": self.film.pk})



class ProiezioneUpdateView(GroupRequiredMixin, UpdateView):
    model = Proiezione
    form_class = ProiezioneForm
    template_name = "cinema/proiezione_form.html"
    group_required = ["gestore_film"]
    superuser_allowed = True
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["film"] = self.object.film
        context["proiezioni_film"] = (
            Proiezione.objects
            .filter(film=self.object.film, data_ora__gte=timezone.now())
            .select_related("sala")
            .order_by("data_ora")
        )
        context["title"] = "Modifica"
        return context
    
    def get_success_url(self):
        film_id = self.object.film.pk
        return reverse_lazy("cinema:film_detail", kwargs={"pk": film_id})



class ProiezioneDeleteView(GroupRequiredMixin, DeleteView):
    model = Proiezione
    template_name = "cinema/proiezione_delete.html"
    group_required = ["gestore_film"]
    superuser_allowed = True
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["film"] = self.object.film
        return context

    def get_success_url(self):
        film_id = self.object.film.pk
        return reverse_lazy("cinema:film_detail", kwargs={"pk": film_id})

