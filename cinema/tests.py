from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.permissions import GROUP_GESTORE
from cinema.models import Film, Proiezione, Sala

User = get_user_model()


class CinemaManagerRulesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.g_gestore = Group.objects.create(name=GROUP_GESTORE)
        cls.gestore = User.objects.create_user(username="gest", password="pass", email="g@x.it")
        cls.gestore.groups.add(cls.g_gestore)

        cls.sala = Sala.objects.create(nome="Sala 1")

        cls.film1 = Film.objects.create(
            titolo="Film 1",
            descrizione="...",
            data_uscita=timezone.localdate() - timedelta(days=30),
            durata_minuti=120,
            genere="Test",
            regista="Reg",
            cast_principale="Cast",
            locandina_url="https://example.com/poster.jpg",
            uscita_locale=timezone.localdate() - timedelta(days=9),
            in_programmazione=timezone.localdate() - timedelta(days=10),
        )

        cls.film2 = Film.objects.create(
            titolo="Film 2",
            descrizione="...",
            data_uscita=timezone.localdate() - timedelta(days=30),
            durata_minuti=120,
            genere="Test",
            regista="Reg",
            cast_principale="Cast",
            locandina_url="https://example.com/poster2.jpg",
            uscita_locale=timezone.localdate() - timedelta(days=9),
            in_programmazione=timezone.localdate() - timedelta(days=10),
        )

    def setUp(self):
        self.client.force_login(self.gestore)

    def test_non_si_puo_eliminare_film_con_proiezione_futura(self):
        # Arrange: proiezione futura associata al film
        Proiezione.objects.create(
            film=self.film1,
            sala=self.sala,
            data_ora=timezone.now() + timedelta(days=2),
        )

        # Act: apro la pagina elimina
        url = reverse("cinema:film_elimina", kwargs={"pk": self.film1.id})
        resp = self.client.get(url)

        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Questo film ha proiezioni associate")

    def test_non_sovrappore_i_film(self):
        # Arrange: esiste già una proiezione in quella sala
        start = timezone.now() + timedelta(days=3)
        Proiezione.objects.create(
            film=self.film1,
            sala=self.sala,
            data_ora=start,
        )

        # Act: provo a creare una seconda proiezione che inizia dentro la durata 
        overlap_start = start + timedelta(minutes=60)  # il film dura 120 + buffer 15 => conflitto sicuro

        url = reverse("cinema:proiezione_crea", kwargs={"film_id": self.film2.id})
        resp = self.client.post(
            url,
            data={"sala": self.sala.id, "data_ora": overlap_start.strftime("%Y-%m-%d %H:%M:%S")},
        )

        # Assert:
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Proiezione.objects.filter(sala=self.sala).count(), 1)
