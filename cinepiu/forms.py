from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

class CreaUtenteCliente(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user
    
class CreaUtenteGestoreFilm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit)
        g = Group.objects.get(name='gestore_film')
        g.user_set.add(user)
        return user

class CreaUtenteSegretario(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit)
        g = Group.objects.get(name='segretario')
        g.user_set.add(user)
        return user