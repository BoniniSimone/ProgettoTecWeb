from datetime import timedelta
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from sales.models import Biglietto
from .models import User
from django.views.generic import ListView
from django.db.models import Q
from .permissions import can_manage_users, can_delete_user, STAFF_GROUPS
from django.views import View
from .permissions import is_cliente 
from braces.views import GroupRequiredMixin

@login_required
def prenotazioni_utente(request, user_id):
    if not can_manage_users(request.user):
        messages.error(request, "Non autorizzato.")
        return redirect("accounts:user_list")

    target = get_object_or_404(User, id=user_id)

    if not is_cliente(target):
        messages.error(request, "Puoi vedere le prenotazioni solo degli utenti comuni.")
        return redirect("accounts:user_list")

    now = timezone.now()
    qs = (
        Biglietto.objects
        .filter(utente=target)
        .select_related("proiezione__film", "proiezione__sala", "posto")
        .order_by("-proiezione__data_ora")
    )

    items = []
    for b in qs:
        can_cancel = now < (b.proiezione.data_ora - timedelta(hours=1))
        items.append({"b": b, "can_cancel": can_cancel})

    # riuso lo stesso template, ma passando un utente "profilo"
    return render(request, "accounts/mie_prenotazioni.html", {
        "items": items,
        "now": now,
        "profile_user": target,   # nuovo
        "as_staff_view": True,    # nuovo
    })


class ToggleSocioView(View):
    def post(self, request, user_id):
        if not request.user.is_authenticated or not can_manage_users(request.user):
            messages.error(request, "Non autorizzato.")
            return redirect("accounts:user_list")

        target = get_object_or_404(User, id=user_id)

        # Solo utenti comuni
        if not is_cliente(target):
            messages.error(request, "Puoi rendere socio solo un utente comune.")
            return redirect("accounts:user_list")

        target.socio = not target.socio
        target.save(update_fields=["socio"])

        messages.success(request, "Stato socio aggiornato.")
        return redirect("accounts:user_list")

class UserListView(GroupRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    group_required = ["segretario", "gestore_film"]
    superuser_allowed = True
    raise_exception = True

    def get_queryset(self):
        return User.objects.all().order_by("username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        staff_users = User.objects.filter(
            Q(groups__name__in=STAFF_GROUPS)
        ).distinct()

        client_users = User.objects.exclude(
            id__in=staff_users.values_list("id", flat=True)
        )

        ctx["staff_users"] = staff_users
        ctx["client_users"] = client_users
        return ctx


class UserDeleteView(View):
    def post(self, request, user_id):
        if not request.user.is_authenticated or not can_manage_users(request.user):
            messages.error(request, "Non autorizzato.")
            return redirect("accounts:user_list")

        target = get_object_or_404(User, id=user_id)

        if Biglietto.objects.filter(utente=target).exists():
            messages.error(request, "Non puoi eliminare un utente che ha prenotazioni.")
            return redirect("accounts:user_list")

        # Evita cancellazioni pericolose
        if target.is_superuser:
            messages.error(request, "Non puoi eliminare un amministratore.")
            return redirect("accounts:user_list")

        if target == request.user:
            messages.error(request, "Non puoi eliminare te stesso.")
            return redirect("accounts:user_list")

        if not can_delete_user(request.user, target):
            messages.error(request, "Non puoi eliminare questo utente.")
            return redirect("accounts:user_list")

        target.delete()
        messages.success(request, "Utente eliminato.")
        return redirect("accounts:user_list")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registrazione completata.")
            return redirect("cinema:programmazione")  # adatta
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def mie_prenotazioni(request):
    now = timezone.now()

    qs = (
        Biglietto.objects
        .filter(utente=request.user)
        .select_related("proiezione__film", "proiezione__sala", "posto")
        .order_by("-proiezione__data_ora")
    )

    items = []
    for b in qs:
        can_cancel = now < (b.proiezione.data_ora - timedelta(hours=1))
        items.append({
            "b": b,
            "can_cancel": can_cancel,
        })

    return render(request, "accounts/mie_prenotazioni.html", {
        "items": items,
        "now": now,
    })
