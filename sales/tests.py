from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from cinema.models import Film, Proiezione, Sala, Posto
from sales.models import Biglietto

User = get_user_model()


class PrenotaViewRulesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="u", password="pass", email="u@x.it")
        cls.sala = Sala.objects.create(nome="Sala 1")
        cls.posto1 = Posto.objects.create(sala=cls.sala, fila="A", numero_posto="1")

        cls.film = Film.objects.create(
            titolo="Film Test",
            descrizione="...",
            data_uscita=timezone.localdate() - timedelta(days=30),
            durata_minuti=120,
            genere="Test",
            regista="Reg",
            cast_principale="Cast",
            locandina_url="https://example.com/poster.jpg",
            uscita_locale = timezone.localdate() - timedelta(days=10),
            in_programmazione=timezone.localdate() - timedelta(days=10),  # già in programmazione
        )

    def setUp(self):
        self.client.force_login(self.user)

    # Un utente non può prenotare per una proiezione passata
    def test_utente_non_puo_prenotare_proiezioni_passate(self):
        # Arrange: proiezione nel passato
        past_show = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.now() - timedelta(days=1),
        )

        # Act: provo a prenotare un posto
        url = reverse("sales:prenota", kwargs={"proiezione_id": past_show.id})
        resp = self.client.post(url, data={"seat_ids": str(self.posto1.id)}, follow=True)

        # Assert: nessun biglietto creato
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Biglietto.objects.count(), 0)


    # Un utente non può prenotare un posto già occupato
    def test_utente_non_puo_prenotare_posto_gia_occupato(self):
        # Arrange: proiezione futura
        future_show = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.now() + timedelta(days=1),
        )

        # Creo già un biglietto per quel posto (posto occupato)
        Biglietto.objects.create(proiezione=future_show, posto=self.posto1, utente=self.user)

        # Act: provo a prenotare lo stesso posto di nuovo
        url = reverse("sales:prenota", kwargs={"proiezione_id": future_show.id})
        resp = self.client.post(url, data={"seat_ids": str(self.posto1.id)}, follow=True)

        # Assert: non deve creare un secondo biglietto
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Biglietto.objects.filter(proiezione=future_show, posto=self.posto1).count(), 1)


    # Non si possono prenotare i film non ancora in programmazione (anche se i gestori hanno già fissato delle proiezioni)
    def test_utente_non_puo_prenotare_film_non_ancora_in_programmazione(self):
        # Arrange: film NON ancora in programmazione (domani)
        film_future = Film.objects.create(
            titolo="Film Non In Programmazione",
            descrizione="...",
            data_uscita=timezone.localdate() - timedelta(days=30),
            durata_minuti=100,
            genere="Test",
            regista="Reg",
            cast_principale="Cast",
            locandina_url="https://example.com/poster2.jpg",
            uscita_locale=timezone.localdate() + timedelta(days=1),
            in_programmazione=timezone.localdate() + timedelta(days=1),
        )

        show = Proiezione.objects.create(
            film=film_future,
            sala=self.sala,
            data_ora=timezone.now() + timedelta(days=2),
        )

        # Act
        url = reverse("sales:prenota", kwargs={"proiezione_id": show.id})
        resp = self.client.post(url, data={"seat_ids": str(self.posto1.id)}, follow=True)

        # Assert: nessun biglietto creato
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Biglietto.objects.filter(proiezione=show).count(), 0)
