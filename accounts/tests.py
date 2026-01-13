from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.permissions import GROUP_SEGRETARIO
from cinema.models import Film, Proiezione, Sala, Posto
from sales.models import Biglietto

User = get_user_model()


class UserDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.g_segretario = Group.objects.create(name=GROUP_SEGRETARIO)
        cls.staff = User.objects.create_user(username="seg", password="pass", email="segre@segre.it")
        cls.staff.groups.add(cls.g_segretario)

        cls.sala = Sala.objects.create(nome="Sala 1")
        cls.posto = Posto.objects.create(sala=cls.sala, fila="A", numero_posto="1")

        cls.film = Film.objects.create(
            titolo="Film Test",
            descrizione="...",
            data_uscita=timezone.localdate() - timedelta(days=10),
            durata_minuti=120,
            genere="Test",
            regista="Reg",
            cast_principale="Cast",
            locandina_url="https://example.com/poster.jpg",
        )

    def setUp(self):
        self.client.force_login(self.staff)

    # Non posso eliminare un utente che ha delle prenotazioni future attive
    def test_delete_bloccata_per_utente_con_prenotazioni_future(self):
        target = User.objects.create_user(username="target", password="pass", email="target@target.it")

        future_show = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.now() + timedelta(days=1),
        )
        Biglietto.objects.create(proiezione=future_show, posto=self.posto, utente=target)

        url = reverse("accounts:user_delete", kwargs={"user_id": target.id})
        resp = self.client.post(url, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(id=target.id).exists())
    
    # Posso eliminare un utente anche se ha delle prenotazioni se queste sono passate
    def test_delete_permessa_per_utente_con_solo_prenotazioni_passate(self):
        target = User.objects.create_user(username="target2", password="pass", email="target2@target.it")

        past_show = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.now() - timedelta(days=2),
        )
        Biglietto.objects.create(proiezione=past_show, posto=self.posto, utente=target)

        url = reverse("accounts:user_delete", kwargs={"user_id": target.id})
        resp = self.client.post(url, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(id=target.id).exists())

