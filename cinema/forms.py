from django import forms
from django.utils import timezone
from .models import Proiezione, Film
from django.core.exceptions import ValidationError

class ProiezioneForm(forms.ModelForm):
    class Meta:
        model = Proiezione
        fields = [
            "sala", 
            "data_ora"
        ]
        widgets = {
            "sala": forms.Select(attrs={"class": "form-select"}),
            "data_ora": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned_data = super().clean()

        sala = cleaned_data.get("sala")
        data_ora = cleaned_data.get("data_ora")

        if not sala or not data_ora or not self.film:
            return cleaned_data

        proiezione = self.instance
        proiezione.sala = sala
        proiezione.data_ora = data_ora
        proiezione.film = self.film

        try:
            proiezione.clean()
        except ValidationError as e:
            self.add_error(None, e)

        return cleaned_data


    def __init__(self, *args, **kwargs):
        self.film = kwargs.pop("film", None)  # lo passeremo dalla view
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            if self.instance.pk and self.instance.data_ora:
                dt = timezone.localtime(self.instance.data_ora)
                self.initial["data_ora"] = dt.replace(second=0, microsecond=0)
            

class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = [
            "titolo",
            "regista",
            "cast_principale",
            "descrizione",
            "genere",
            "durata_minuti",
            "data_uscita",
            "uscita_locale",
            "in_programmazione",
            "locandina_url",
            "trailer_url",
            "rassegna",
        ]
        widgets = {
            "titolo": forms.TextInput(attrs={"class": "form-control"}),
            "descrizione": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "durata_minuti": forms.NumberInput(attrs={"class": "form-control"}),
            "data_uscita": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "uscita_locale": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "in_programmazione": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "trailer_url": forms.URLInput(attrs={"class": "form-control"}),
            "rassegna": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "locandina_url": forms.URLInput(attrs={"class": "form-control"}),
            "genere": forms.TextInput(attrs={"class": "form-control"}),
            "regista": forms.TextInput(attrs={"class": "form-control"}),
            "cast_principale": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
