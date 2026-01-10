from django.db import models
from django.conf import settings

class Biglietto(models.Model):
    class Stato(models.TextChoices):
        PRENOTATO = "PRE", "Prenotato"
        PAGATO = "PAG", "Pagato"
        ANNULLATO = "ANN", "Annullato"

    proiezione = models.ForeignKey("cinema.Proiezione", on_delete=models.CASCADE, related_name="biglietti")
    posto = models.ForeignKey("cinema.Posto", on_delete=models.PROTECT)
    prezzo = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)

    # online
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True) #imposto blank=True per i biglietti venduti in segreteria che non hanno bisogno di un utente associato

    # segreteria (telefono / in presenza)
    nome_cliente = models.CharField(max_length=120, blank=True)
    telefono_cliente = models.CharField(max_length=30, blank=True)

    stato = models.CharField(max_length=3, choices=Stato.choices, default=Stato.PRENOTATO)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["proiezione", "posto"], name="uniq_posto_per_proiezione"),
        ]

