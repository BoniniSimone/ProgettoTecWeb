from __future__ import annotations
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.utils import timezone
from cinema.models import Film, Sala, Posto, Proiezione
from sales.models import Biglietto


class Command(BaseCommand):
    help = "Popola il database con dati di test (sale, posti, film, proiezioni, prenotazioni, utenti demo)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Cancella i dati (prenotazioni, proiezioni, posti, sale, film) prima di ricreare il seed.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Quanti giorni di programmazione creare (default: 7).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Seed random per rendere riproducibile la generazione (default: 42).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        days = options["days"]
        do_reset = options["reset"]

        if do_reset:
            self._reset_data()

        self.stdout.write(self.style.NOTICE("Creazione gruppi/utenti demo..."))
        self._crea_gruppi_e_utenti()

        self.stdout.write(self.style.NOTICE("Creazione sale + posti..."))
        sale = self._crea_sale_e_posti()

        self.stdout.write(self.style.NOTICE("Creazione film..."))
        films = self._crea_film()

        self.stdout.write(self.style.NOTICE("Creazione proiezioni..."))
        proiezioni = self._crea_proiezioni(films, sale, days=days)

        self.stdout.write(self.style.NOTICE("Creazione prenotazioni di esempio..."))
        self._crea_biglietti(proiezioni)

        self.stdout.write(self.style.SUCCESS("Seed completato con successo."))

    def _reset_data(self):
        # Ordine importante
        Biglietto.objects.all().delete()
        Proiezione.objects.all().delete()
        Posto.objects.all().delete()
        Sala.objects.all().delete()
        Film.objects.all().delete()

        self.stdout.write(self.style.WARNING("Dati cancellati (reset eseguito)."))

    def _crea_gruppi_e_utenti(self):
        """
        Crea gruppi: gestore_film, segretario, cliente.
        Crea anche 2 utenti demo e un superuser se non esistono già.
        """
        User = get_user_model()

        gestore_group, _ = Group.objects.get_or_create(name="gestore_film")
        segretario_group, _ = Group.objects.get_or_create(name="segretario")
        cliente_group, _ = Group.objects.get_or_create(name="cliente")

        cinema_perms = Permission.objects.filter(
            content_type__app_label="cinema",
            codename__in=[
                "add_film", "change_film", "delete_film", "view_film",
                "add_biglietto", "change_biglietto", "delete_biglietto", "view_biglietto",
                "add_sala", "change_sala", "delete_sala", "view_sala",
                "add_posto", "change_posto", "delete_posto", "view_posto",
            ],
        )
        gestore_group.permissions.add(*cinema_perms)

        sales_perms = Permission.objects.filter(
            content_type__app_label="sales",
            codename__in=[
                "add_biglietto", "change_biglietto", "delete_biglietto", "view_biglietto",
            ],
        )
        segretario_group.permissions.add(*sales_perms)

        # Utenti demo
        admin_username = "admin"
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(username=admin_username, email="admin@example.com", password="admin1234")

        gestore_username = "Antonio"
        if not User.objects.filter(username=gestore_username).exists():
            u = User.objects.create_user(username=gestore_username, email="gestore@example.com", password="gestore1234")
            u.groups.add(gestore_group)

        segretario_username = "Claudio"
        if not User.objects.filter(username=segretario_username).exists():
            u = User.objects.create_user(username=segretario_username, email="segretario@example.com", password="segre1234")
            u.groups.add(segretario_group)

        cliente_username = "Francesco"
        if not User.objects.filter(username=cliente_username).exists():
            u = User.objects.create_user(username=cliente_username, email="francesco@example.com", password="francesco1234")
            u.groups.add(cliente_group)
            if hasattr(u, "socio"):
                u.socio = True
                u.save(update_fields=["socio"])


    def _crea_sale_e_posti(self):
        sala1, _ = Sala.objects.get_or_create(nome="Sala 1")
        sala2, _ = Sala.objects.get_or_create(nome="Sala 2")

        def gen_posti(sala, righe=10, posti_per_riga=12):
            for i in range(righe):
                fila = chr(ord("A") + i)  # A, B, C...
                for n in range(1, posti_per_riga + 1):
                    Posto.objects.get_or_create(
                        sala=sala,
                        fila=fila,
                        numero_posto=str(n),
                    )

        gen_posti(sala1, righe=10, posti_per_riga=12)
        gen_posti(sala2, righe=8, posti_per_riga=10)

        return [sala1, sala2]


    def _crea_film(self):
        data = [
            {
                "titolo": "Interstellar",
                "descrizione": "Un viaggio epico attraverso lo spazio e il tempo.",
                "data_uscita": "2014-11-07",
                "durata_minuti": 169, 
                "genere": "Sci-Fi",
                "regista": "Christopher Nolan",
                "cast_principale": "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
                "locandina_url": "https://www.warnerbros.it/wp-content/uploads/2024/10/Interstellar_10%C2%B0-Anniversario_Poster-Italia.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=EIVMVIr3q3Y",
            },
            {
                "titolo": "Il Signore degli Anelli: Il Ritorno del Re",
                "descrizione": "La conclusione epica della trilogia.",
                "data_uscita": "2003-12-17", 
                "durata_minuti": 201,
                "genere": "Fantasy",
                "regista": "Peter Jackson",
                "cast_principale": "Elijah Wood, Ian McKellen, Viggo Mortensen",
                "locandina_url": "https://m.media-amazon.com/images/M/MV5BMTZkMjBjNWMtZGI5OC00MGU0LTk4ZTItODg2NWM3NTVmNWQ4XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=r5X-hFf6Bwo",
                
            },
            {
                "titolo": "Il Cavaliere Oscuro", 
                "durata_minuti": 152, 
                "descrizione": "Il secondo capitolo della trilogia di Batman di Nolan.",
                "data_uscita": "2008-07-18",
                "genere": "Azione",
                "regista": "Christopher Nolan",
                "cast_principale": "Christian Bale, Heath Ledger, Aaron Eckhart",
                "locandina_url": "https://mr.comingsoon.it/imgdb/locandine/big/848.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=yqcDBdk8wpo",
            },
            {
                "titolo": "Il Buono, il Brutto, il Cattivo", 
                "durata_minuti": 161, 
                "descrizione": "Un classico spaghetti western di Sergio Leone.",
                "data_uscita": "1966-12-23",
                "genere": "Western",
                "regista": "Sergio Leone",
                "cast_principale": "Clint Eastwood, Eli Wallach, Lee Van Cleef",
                "locandina_url": "https://pad.mymovies.it/filmclub/2002/08/283/locandina.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=WBXWxuOc2dE",
            },
            {
                "titolo": "Odissea",
                "durata_minuti": 120,
                "descrizione": "Segue Odisseo nel suo pericoloso viaggio verso casa dopo la guerra di Troia, mostrando i suoi incontri con Polifemo, le Sirene, Circe e finendo con la sua riunione con sua moglie Penelope.",
                "data_uscita": "2026-07-17",
                "genere": "Avventura",
                "regista": "Cristopher Nolan",
                "cast_principale": "Matt Damon, Tom Holland, Anne Hathaway, Robert Pattinson",
                "locandina_url": "https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcTOBKoWqowNoULo7-Dq6U455Lcl1_MEtLPhQ8spI-AuFIJbfLWc",
                "trailer_url": "https://www.youtube.com/watch?v=6SbP6gvsrlk",
            },
            {
                "titolo": "Il Sapore della Ciliegia",
                "durata_minuti": 95,
                "descrizione": "Un uomo guida per le colline di Teheran alla ricerca di qualcuno che lo aiuti a morire.",
                "data_uscita": "2025-11-12",
                "genere": "Drammatico",
                "regista": "Abbas Kiarostami",
                "cast_principale": "Homayoun Ershadi, Abdolrahman Bagheri, Badi Olama",
                "locandina_url": "https://www.cinefacts.it/foto/h!Il-sapore-della-ciliegia-locandina-poster-cinefacts.jpg",
                "trailer_url": "https://www.youtube.com/watch?v=J7YkXc1qk8",
                "rassegna": True,
            }
        ]
        films = []
        for f in data:
            film, _ = Film.objects.get_or_create(
                titolo=f["titolo"],
                defaults={
                    "descrizione": f["descrizione"],
                    "data_uscita": f["data_uscita"],
                    "durata_minuti": f["durata_minuti"],
                    "genere": f["genere"],
                    "regista": f["regista"],
                    "cast_principale": f["cast_principale"],
                    "locandina_url": f["locandina_url"],
                    "trailer_url": f["trailer_url"],
                    "rassegna": f.get("rassegna", False),
                },
            )
            films.append(film)
        return films

    def _crea_proiezioni(self, films, sale, days: int):
        proiezioni = []
        now = timezone.now()

        # Fasce orarie tipiche
        times = [(18, 0), (20, 30), (22, 45)]

        for d in range(days):
            day = (now + timedelta(days=d)).date()

            # Evita proiezioni per film non ancora usciti localmente (es. titoli futuri come "Odissea")
            film_ammissibili = [
                f for f in films
                if (getattr(f, "uscita_locale", None) or f.data_uscita) <= day
            ]
            if not film_ammissibili:
                continue

            for sala in sale:
                for (hh, mm) in times:
                    start = timezone.make_aware(
                        timezone.datetime(day.year, day.month, day.day, hh, mm),
                        timezone.get_current_timezone(),
                    )

                    film = random.choice(film_ammissibili)

                    p, _ = Proiezione.objects.get_or_create(
                        film=film,
                        sala=sala,
                        data_ora=start,
                    )
                    proiezioni.append(p)

        return proiezioni

    def _crea_biglietti(self, proiezioni):
        User = get_user_model()
        francesco = User.objects.filter(username="Francesco").first()

        for p in random.sample(proiezioni, k=min(5, len(proiezioni))):
            # prendo 3 posti random della sala della proiezione
            posti = list(Posto.objects.filter(sala=p.sala))
            random.shuffle(posti)

            for posto in posti[:3]:
                # Una prenotazione online (francesco)
                try:
                    Biglietto.objects.create(proiezione=p, posto=posto, utente=francesco)
                except Exception:
                    pass

            posto = random.choice(posti[3:]) if len(posti) > 3 else posti[0]
            try:
                Biglietto.objects.create(
                    proiezione=p,
                    posto=posto,
                    nome_cliente="Cliente Segreteria",
                    telefono_cliente="+39 333 0000000",
                )
            except Exception:
                pass
