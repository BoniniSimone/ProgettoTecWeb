from django.contrib import admin
from .models import Film, Proiezione, Recensione, Sala, Posto

admin.site.register(Film)
admin.site.register(Proiezione)
admin.site.register(Recensione)
admin.site.register(Sala)
admin.site.register(Posto)

# Register your models here.
