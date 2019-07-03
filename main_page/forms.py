from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
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
  cpr = forms.CharField(label='Cpr-nr.')
  name = forms.CharField(label='Navn')
  study_date = forms.DateField(label='Dato (ÅÅÅÅ-MM-DD)')
  rigs_nr = forms.CharField(label='Accessionnummer.')

# Udfyld undersøgelse
class FillStudyDaily(forms.Form):
  factor = forms.IntegerField(label='Fortyndingsfaktor')
  batch = forms.IntegerField(label='Batch')
  standard = forms.IntegerField(label='Standard tælletal')

class Fillpatient_1(forms.Form):
  cpr = forms.CharField(label='Cpr-nr.', required=False)
  name = forms.CharField(label='Navn', required=False)
  sex = forms.CharField(label='Køn', required=False)
  birthdate = forms.DateField(label='Fødselsdato (ÅÅÅÅ-MM-DD)', required=False)
  
class Fillpatient_2(forms.Form):
  height = forms.FloatField(label='Højde (cm)', required=False, min_value=0)
  weight = forms.FloatField(label='Vægt (kg)', required=False, min_value=0)

class Fillexamination(forms.Form):
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før injektion (g)', required=False, min_value=0)
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, min_value=0)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (ÅÅÅÅ-MM-DD)', required=False)  

class Filldosis(forms.Form):
  #std_cnt = forms.IntegerField(label='Standard tælletal', required=False, min_value=0)
  thin_fac = forms.IntegerField(label='Fortyndingsfaktor', required=False, min_value = 0)
  save_fac = forms.BooleanField(required=False, label='Gem')

class FillStudyType(forms.Form):
  types = [
    (0, 'En blødprøve, voksen'),
    (1, 'En blødprøve, barn'),
    (2, 'Flere blødprøver')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())

class FillStudyTest(forms.Form):
  study_time = forms.TimeField(label='Prøvetidspunkt (tt:mm)', required=False)
  study_date = forms.DateField(label='Dato (ÅÅÅÅ-MM-DD)', required=False)

class GetStudy(forms.Form):
  name = forms.CharField(label='Navn', required=False)
  cpr  = forms.CharField(label='Cpr-nr.', required=False)
  Rigs = forms.CharField(label='Accessionnummer', required=False)
  Dato_start = forms.DateField(label='Fra dato (ÅÅÅÅ-MM-DD)', required=False)
  Dato_finish = forms.DateField(label='Til dato (ÅÅÅÅ-MM-DD)', required=False)

class FillThiningFactor(forms.Form):
  thin_fac = forms.FloatField(label='Fortydnings Faktor', min_value=0.0, required=True)

class GetBackupDate(forms.Form):
  dateofmessurement = forms.DateField(label='Backup fra dato (ÅÅÅÅ-MM-DD)', required=False)