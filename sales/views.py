from datetime import timedelta
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from cinema.models import Posto, Proiezione
from .models import Biglietto
from cinema.models import Film
from django.views.generic import DetailView, DeleteView, View
from django.urls import reverse
from braces.views import GroupRequiredMixin
from accounts.permissions import is_operational_staff
from decimal import Decimal


class PrenotazioniFilmView(GroupRequiredMixin, DetailView):
    model = Film
    pk_url_kwarg = "film_id"
    context_object_name = "film"
    template_name = "sales/prenotazioni_film.html"
    group_required = ["segretario", "gestore_film"]
    superuser_allowed = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        film = self.object

        biglietti = (
            Biglietto.objects
            .filter(proiezione__film=film)
            .select_related("proiezione__sala", "proiezione__film", "posto", "utente")
            .order_by("-proiezione__data_ora", "posto__fila", "posto__numero_posto")
        )

        grouped = {} #lo si usa con chiave=Proiezione e valore=Biglietto
        for b in biglietti:
            grouped.setdefault(b.proiezione, []).append(b)

        proiezioni = [{"proiezione": p, "biglietti": grouped[p]} for p in grouped.keys()]
        proiezioni.sort(key=lambda x: x["proiezione"].data_ora, reverse=True)

        ctx["proiezioni"] = proiezioni
        ctx["now"] = timezone.now()
        return ctx



class BigliettoSegnaPagatoView(GroupRequiredMixin, View):
    group_required = ["segretario", "gestore_film"]
    superuser_allowed = True
    
    def post(self, request, pk):
        biglietto = get_object_or_404(Biglietto, pk=pk)
        biglietto.stato = Biglietto.Stato.PAGATO
        biglietto.save(update_fields=["stato"])
        return redirect(request.META.get("HTTP_REFERER", "info"))



class BigliettoStaffDeleteView(GroupRequiredMixin, DeleteView):
    model = Biglietto
    pk_url_kwarg = "biglietto_id"
    group_required = ["segretario", "gestore_film"]
    superuser_allowed = True
    raise_exception = True

    def get(self, request, *args, **kwargs):
        messages.error(request, "Operazione non valida.")
        return redirect("cinema:programmazione")

    def get_success_url(self):
        film_id = self.object.proiezione.film_id
        messages.success(self.request, "Biglietto eliminato.")
        return reverse("sales:prenotazioni_film", kwargs={"film_id": film_id})


@login_required
def prenota(request, proiezione_id):
    proiezione = get_object_or_404(
        Proiezione.objects.select_related("film", "sala"),
        id=proiezione_id,
    )

    # blocca prenotazioni su proiezioni passate
    now = timezone.now()
    if proiezione.data_ora < now:
        messages.error(request, "Non puoi prenotare: la proiezione è già passata.")
        return redirect("cinema:programmazione")
    
    # blocca prenotazioni se il film non è ancora in programmazione
    if proiezione.film.in_programmazione and proiezione.film.in_programmazione > now.date():
        messages.error(request, "Non puoi prenotare: il film non è ancora in programmazione.")
        return redirect("cinema:prossimamente")

    # -------- POST: crea i biglietti --------
    if request.method == "POST":
        # seat_ids arriva come "12,15,18"
        seat_ids_raw = (request.POST.get("seat_ids") or "").strip()
        seat_ids = [s.strip() for s in seat_ids_raw.split(",") if s.strip()] #alla fine abbiamo una semplice lista di ID

        if not seat_ids:
            messages.error(request, "Seleziona almeno un posto.")
            return redirect("sales:prenota", proiezione_id=proiezione.id)
        
        staff_mode = is_operational_staff(request.user)

        prezzo_unitario = Decimal("8.00")
        if (not staff_mode) and getattr(request.user, "socio", False):
            prezzo_unitario = Decimal("6.00")

        nome_cliente = (request.POST.get("nome_cliente") or "").strip()
        telefono_cliente = (request.POST.get("telefono_cliente") or "").strip()

        if staff_mode:
            # obbliga almeno un dato cliente
            if not (nome_cliente or telefono_cliente):
                messages.error(request, "Inserisci nome e telefono del cliente.")
                return redirect("sales:prenota", proiezione_id=proiezione.id)


        try:
            with transaction.atomic():  # le prossime operazioni devono avvenire tutte insieme

                if not staff_mode:
                    gia_prenotati = (
                        Biglietto.objects
                        .select_for_update()
                        .filter(proiezione=proiezione, utente=request.user, stato=Biglietto.Stato.PRENOTATO)
                        .count()
                    )
                    if gia_prenotati + len(seat_ids) > 2:
                        messages.error(request, "Puoi prenotare al massimo 2 biglietti per questa proiezione.")
                        return redirect("sales:prenota", proiezione_id=proiezione.id)
                    
                # Verifica che i posti siano della sala della proiezione (e lock per concorrenza)
                posti = list(
                    Posto.objects.select_for_update()
                    .filter(id__in=seat_ids, sala=proiezione.sala)
                )

                if len(posti) != len(seat_ids):
                    messages.error(request, "Uno o più posti non sono validi per questa sala.")
                    return redirect("sales:prenota", proiezione_id=proiezione.id)

                # Crea un biglietto per ogni posto
                Biglietto.objects.bulk_create([
                    Biglietto(
                        proiezione=proiezione,
                        posto=posto,
                        prezzo=prezzo_unitario,
                        utente=None if staff_mode else request.user,
                        nome_cliente=nome_cliente if staff_mode else "",
                        telefono_cliente=telefono_cliente if staff_mode else "",
                        stato=Biglietto.Stato.PRENOTATO,
                    )
                    for posto in posti
                ])


        except IntegrityError:
            # Scatta grazie al vincolo uniq_posto_per_proiezione (proiezione, posto)
            messages.error(request, "Alcuni posti sono appena stati prenotati da un altro utente. Riprova.")
            return redirect("sales:prenota", proiezione_id=proiezione.id)

        messages.success(request, "Prenotazione completata! Biglietti creati.")
        return redirect("sales:prenota", proiezione_id=proiezione.id)  # o profilo

    # -------- GET --------
    posti = (
        Posto.objects
        .filter(sala=proiezione.sala)
        .order_by("fila", "numero_posto")
    )

    occupati = set(
        Biglietto.objects
        .filter(proiezione=proiezione)
        .values_list("posto_id", flat=True)
    )

    righe = []
    riga_corrente = None
    buffer_posti = []

    for posto in posti:
        if riga_corrente is None:
            riga_corrente = posto.fila

        if posto.fila != riga_corrente:
            righe.append({"fila": riga_corrente, "posti": buffer_posti})
            riga_corrente = posto.fila
            buffer_posti = []

        buffer_posti.append(
            {
                "id": posto.id,
                "label": f"{posto.fila}{posto.numero_posto}",
                "occupied": posto.id in occupati,
            }
        )

    if riga_corrente is not None:
        righe.append({"fila": riga_corrente, "posti": buffer_posti})

    context = {
        "proiezione": proiezione,
        "righe": righe,
        "now": timezone.now(),
        "staff_mode": is_operational_staff(request.user),
    }
    return render(request, "sales/prenota.html", context)


@login_required
def annulla_biglietto(request, biglietto_id):
    biglietto = get_object_or_404(
        Biglietto.objects.select_related("proiezione"),
        id=biglietto_id,
        utente=request.user,   # impedisce annulli di altri utenti
    )

    # Per sicurezza: accetta solo POST (evita annulli via GET)
    if request.method != "POST":
        messages.error(request, "Operazione non valida.")
        return redirect("accounts:mie_prenotazioni")

    now = timezone.now()
    limite = biglietto.proiezione.data_ora - timedelta(hours=1)

    # non annullabile da 1 ora prima della proiezione
    if now >= limite:
        messages.error(request, "Non puoi annullare: manca meno di 1 ora alla proiezione.")
        return redirect("accounts:mie_prenotazioni")

    biglietto.delete()
    messages.success(request, "Prenotazione annullata. Il posto è stato liberato.")
    return redirect("accounts:mie_prenotazioni")

