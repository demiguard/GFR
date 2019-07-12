from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
import main_page.models as models
import main_page.libs.server_config as server_config


# User settings form
class SettingsForm(ModelForm):
  class Meta:
    model = models.Config
    fields = [
      'accepted_procedures',
      'ris_aet',
      'ris_ip',
      'ris_port',
      'ris_calling',
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

class AddUserForm(ModelForm):
  class Meta:
    model = models.User
    fields = [
      'username',
      'password',
    ]

    labels = {
      'username': 'Brugernavn'
    }

  confirm_pass = forms.CharField(max_length=120, label="Gentag password", widget=forms.PasswordInput())

  # List available hospital choices from the database
  hosp_depart_choices = [ ]

  for department in models.Department.objects.all():
    choice_str = f"{department.hospital.name} - {department.name}"
    hosp_depart_choices.append((department.id, choice_str))

  hosp_depart = forms.ChoiceField(choices=hosp_depart_choices, label="Afdeling")

  # List available user groups
  group_choices = [(group.id, group.name) for group in reversed(models.UserGroup.objects.all())]

  group = forms.ChoiceField(choices=group_choices, label="Bruger gruppe")


class AddHospitalForm(ModelForm):
  class Meta:
    model = models.Hospital
    fields = [
      'name',
      'short_name',
      'address'
    ]

    labels = {
      'name': 'Navn',
      'short_name': 'Forkortelse',
      'address': 'Addresse',
    }


class AddDepartmentForm(ModelForm):
  class Meta:
    model = models.Department
    fields = [
      'name',
    ]

    labels =  {
      'name': 'Navn',
    }

  # List available hospitals
  hosp_choices = [(hospital.id, hospital.name) for hospital in models.Hospital.objects.all()]

  hospital = forms.ChoiceField(choices=hosp_choices)


class AddConfigForm(ModelForm):
  class Meta:
    model = models.Config
    fields = [
      'ris_aet',
      'ris_ip',
      'ris_port',
      'ris_calling',
      'pacs_aet',
      'pacs_ip',
      'pacs_port',
      'pacs_calling'
    ]


class SearchHandledExaminationsForm(ModelForm):
  class Meta:
    model = models.HandledExaminations
    fields = [
      'accession_number'
    ]

    labels = {
      'accession_number': 'Accession nummer'
    }


class GetBackupDate(forms.Form):
  dateofmessurement = forms.DateField(label='Backup fra dato (ÅÅÅÅ-MM-DD)', required=False)
