from django.conf import settings
from django.db import models
from urllib.parse import urlparse, parse_qs
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class Film(models.Model):
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField()
    data_uscita = models.DateField()
    durata_minuti = models.PositiveIntegerField()
    genere = models.CharField(max_length=100)
    regista = models.CharField(max_length=100)
    cast_principale = models.TextField()
    locandina_url = models.URLField()
    trailer_url = models.URLField(blank=True, null=True)
    rassegna = models.BooleanField(default=False) #Booleano che indica se un film appartiene alla rassegna
    uscita_locale = models.DateField(blank=True, null=True) #Indica qunado il film uscirà nel nostro cinema (non ci sono controlli, quindi un film potrebbe uscire in una data precedente al giorno della prima proiezione)
    in_programmazione = models.DateField(blank=True, null=True) #Indica quando un film passa nella sezione "Programmazione" del sito e diventa in prenotabile

    #Trasforma un URL normale in un URL embed
    @property
    def trailer_embed_url(self): 
        if not self.trailer_url:
            return ""

        url = self.trailer_url.strip()
        p = urlparse(url) # divide l'URL in componenti (schema, host, path...)

        host = (p.netloc or "").lower()
        path = (p.path or "").strip("/") # strip rimuove, in questo caso, tutti i caratteri "/" da inizio e da infondo alla stringa

        # già in formato embed
        if "youtube.com" in host and path.startswith("embed/"):
            return url

        # youtu.be/<id>
        if "youtu.be" in host and path:
            video_id = path.split("/")[0] # prende solo l'elemento con indice 0 di quelli che ha splittato
            return f"https://www.youtube.com/embed/{video_id}"

        # youtube.com/watch?v=<id>
        if "youtube.com" in host:
            qs = parse_qs(p.query) # parse_sq prende la parte di query e la trasforma in un dizionario
            video_id = (qs.get("v") or [""])[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

        #non riconosciuto
        return url

    def clean(self):
        errors = {} #dizionario che ci servirà per indicare di che errore si tratta (se si presenta un errore)

        # vincolo: uscita_locale >= data_uscita (l'uscita locale non può avvenire prima di quando il film esce in un paese)
        if self.uscita_locale and self.data_uscita and self.uscita_locale < self.data_uscita:
            errors["uscita_locale"] = "La data di uscita locale non può essere precedente alla data di uscita."

        # vincolo: in_programmazione <= uscita_locale (se si vuole mettere un film in programmazione prima che esca si può fare, ma non dopo il giorno che abbiamo indicato di uscita)
        if self.in_programmazione and self.uscita_locale and self.in_programmazione > self.uscita_locale:
            errors["in_programmazione"] = "La data 'in programmazione' non può essere successiva all'uscita locale."

        if errors:
            raise ValidationError(errors)
        
    def save(self, *args, **kwargs):
        if self.uscita_locale is None:
            self.uscita_locale = self.data_uscita

        if self.in_programmazione is None:
            self.in_programmazione = self.uscita_locale
        
        self.full_clean()
        return super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Film"
    
    def __str__(self):
        return self.titolo




class Proiezione(models.Model):
    film = models.ForeignKey(Film, on_delete=models.PROTECT)
    sala = models.ForeignKey('Sala', on_delete=models.PROTECT)
    data_ora = models.DateTimeField()

    BUFFER_MINUTI = 15  # tempo minimo tra un film e l'altro

    def clean(self):
        errors = {}

        # 1) vincolo: data_ora >= uscita_locale del film
        if self.film_id and self.data_ora and self.film.uscita_locale:
            if self.data_ora.date() < self.film.uscita_locale:
                errors["data_ora"] = (
                    "La proiezione non può essere precedente all'uscita locale del film "
                    f"({self.film.uscita_locale:%d/%m/%Y})."
                )

        # 2) vincolo: no sovrapposizioni in sala
        if self.film_id and self.sala_id and self.data_ora:
            inizio = self.data_ora
            fine = inizio + timedelta( 
                minutes=int(self.film.durata_minuti) + int(self.BUFFER_MINUTI)
            )

            qs = Proiezione.objects.filter(sala_id=self.sala_id).select_related("film")
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            # 1 Cerco se esiste una proiezione che inizia dentro il nostro intervallo della proiezione
            if qs.filter(data_ora__gte=inizio, data_ora__lt=fine).exists():
                errors["data_ora"] = f"La sala è già occupata: esiste una proiezione di {qs.filter(data_ora__gte=inizio, data_ora__lt=fine).first().film.titolo} che inizia prima che il film che si vuole inserire finisca."

            # 2 La proiezione precedente deve finire prima del nostro inizio
            else:
                prev = qs.filter(data_ora__lt=inizio).order_by("-data_ora").first()
                if prev:
                    prev_end = prev.data_ora + timedelta(
                        minutes=int(prev.film.durata_minuti) + int(self.BUFFER_MINUTI)
                    )
                    if prev_end > inizio:
                        errors["data_ora"] = (
                            "La sala è già occupata: conflitto con la proiezione precedente "
                            f"('{prev.film.titolo}' alle {prev.data_ora:%d/%m/%Y %H:%M})."
                        )

        if errors:
            raise ValidationError(errors)    

    class Meta:
        verbose_name_plural = "Proiezioni"
        constraints = [
            models.UniqueConstraint(
                fields=["sala", "data_ora"], 
                name="uniq_proiezione_sala_orario"
            )
        ]

    def __str__(self):
        return f"{self.film.titolo} - {self.data_ora} in {self.sala}"




class Recensione(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    autore = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenuto = models.TextField()
    valutazione = models.IntegerField()
    create_at = models.DateTimeField(auto_now_add=True) #con auto_now_add si salva in automatico la data di creazione della recensione

    class Meta:
        verbose_name_plural = "Recensioni"
        ordering = ["-create_at", "-id"]

    def __str__(self):
        return f"Recensione di {self.autore} per {self.film.titolo}"




class Sala(models.Model):
    nome = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Sale"

    def __str__(self):
        return self.nome
    



class Posto(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    numero_posto = models.CharField(max_length=10)
    fila = models.CharField(max_length=5)

    class Meta:
        verbose_name_plural = "Posti"
        constraints = [
            models.UniqueConstraint(
                fields=["sala", "fila", "numero_posto"],
                name="uniq_posto_per_sala"
            )
        ]

    def __str__(self):
        return f"Sala: {self.sala.nome}, Posto: {self.fila}{self.numero_posto}"
