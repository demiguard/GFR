from django import forms
from django.forms import ModelForm
from main_page.models import Config

# User settings form
class SettingsForm(ModelForm):
  class Meta:
    model = Config
    fields = [
      'accepted_procedures',
      'rigs_aet',
      'rigs_ip',
      'rigs_port',
      'rigs_calling',
      'pacs_aet',
      'pacs_ip',
      'pacs_port',
      'pacs_calling'
    ]

# Login form
class LoginForm(forms.Form):
  username = forms.CharField()
  password = forms.CharField(widget=forms.PasswordInput())

# Ny undersøgelse
class NewStudy(forms.Form):
  cpr = forms.IntegerField(label='Cpr. nr.')
  name = forms.CharField(label='Navn')
  study_date = forms.DateField(label='Dato (YYYY-MM-DD)')
  rigs_nr = forms.CharField(label='RIS nr.')

# Udfyld undersøgelse
class FillStudyDaily(forms.Form):
  factor = forms.IntegerField(label='Fortyndingsfaktor')
  batch = forms.IntegerField(label='Batch')
  standard = forms.IntegerField(label='Standard tælletal')

class Fillpatient_1(forms.Form):
  cpr = forms.CharField(label='Cpr nr.', required=False)
  name = forms.CharField(label='Navn', required=False)
  sex = forms.CharField(label='Køn', required=False)
  age = forms.FloatField(label='Alder', required=False, min_value=0)
  
class Fillpatient_2(forms.Form):
  height = forms.FloatField(label='Højde (cm)', required=False, min_value=0)
  weight = forms.FloatField(label='Vægt (kg)', required=False, min_value=0)

class Fillexamination(forms.Form):
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før Injektion (g)', required=False, min_value=0)
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, min_value=0)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (YYYY-MM-DD)', required=False)  

class Filldosis(forms.Form):
  std_cnt = forms.IntegerField(label='Standard tælletal', required=False, min_value=0)
  thin_fac = forms.IntegerField(label='Faktor', required=False, min_value = 0)

class FillStudyType(forms.Form):
  types = [
    (0, 'Et punkt voksen'),
    (1, 'Et punkt barn'),
    (2, 'Flere Prøve, inc 24 timer prøve, børn og voksne')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())

class FillStudyTest(forms.Form):
  study_time = forms.TimeField(label='Prøvetidspunkt (tt:mm)', required=False)
  study_date = forms.DateField(label='Dato (YYYY-MM-DD)', required=False)

class GetStudy(forms.Form):
  name = forms.CharField(label='Navn', required=False)
  cpr  = forms.CharField(label='Cpr nr.', required=False)
  Rigs = forms.CharField(label='Accession nummer', required=False)
  Dato_start = forms.DateField(label='Fra dato (YYYY-MM-DD)', required=False)
  Dato_finish = forms.DateField(label='Til dato (YYYY-MM-DD)', required=False)
