from django import forms

import main_page.models as models
import main_page.libs.server_config as server_config
from main_page.libs.enums import GENDER_NAMINGS


# Login form
class LoginForm(forms.Form):
  username = forms.CharField()
  password = forms.CharField(widget=forms.PasswordInput())


# Ny undersøgelse
class NewStudy(forms.Form):
  cpr = forms.CharField(label='Cpr-nr.')
  name = forms.CharField(label='Navn')
  study_date = forms.DateField(label='Dato (DD-MM-ÅÅÅÅ)')
  rigs_nr = forms.CharField(label='Accessionnummer.')


class Fillpatient_1(forms.Form):
  cpr = forms.CharField(label='Cpr-nr.', required=False)
  name = forms.CharField(label='Navn', required=False)
  
  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]
  sex = forms.ChoiceField(choices=sex_options, label='Køn', required=False)
  
  birthdate = forms.DateField(label='Fødselsdato (DD-MM-ÅÅÅÅ)', required=False)

class Fillpatient_2(forms.Form):
  height = forms.FloatField(label='Højde (cm)', required=False, min_value=0)
  weight = forms.FloatField(label='Vægt (kg)', required=False, min_value=0)


class Fillexamination(forms.Form):
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før injektion (g)', required=False, min_value=0)
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, min_value=0)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (DD-MM-ÅÅÅÅ)', required=False)  


class Filldosis(forms.Form):
  #std_cnt = forms.IntegerField(label='Standard tælletal', required=False, min_value=0)
  thin_fac = forms.IntegerField(label='Fortyndingsfaktor', required=False, min_value = 0)
  save_fac = forms.BooleanField(required=False, label='Gem')


class FillStudyType(forms.Form):
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())


class FillStudyTest(forms.Form):
  study_time = forms.TimeField(label='Prøvetidspunkt (tt:mm)', required=False)
  study_date = forms.DateField(label='Dato (DD-MM-ÅÅÅÅ)', required=False)

  def __init__(self, *args, **kwargs):
    super(FillStudyTest, self).__init__(*args, **kwargs)

    # Add bootstrap class to fields
    for _, field in self.fields.items():
      field.widget.attrs['class'] = 'form-control'


class GetStudy(forms.Form):
  name = forms.CharField(label='Navn', required=False)
  cpr  = forms.CharField(label='Cpr-nr.', required=False)
  Rigs = forms.CharField(label='Accessionnummer', required=False)
  Dato_start = forms.DateField(label='Fra dato (DD-MM-ÅÅÅÅ)', required=False)
  Dato_finish = forms.DateField(label='Til dato (DD-MM-ÅÅÅÅ)', required=False)


# --- EDIT FORMS START --- #
class EditUserForm(forms.ModelForm):
  class Meta:
    model = models.User
    fields = [
      'username',
    ]

    labels = {
      'username': 'Brugernavn'
    }

  def __init__(self, *args, **kwargs):
    # Call the base class to allow the form to be constructed using templating
    # This allows for access to self.fields
    super(EditUserForm, self).__init__(*args, **kwargs)

    # Get object instance this form is instantiated with
    obj_instance = kwargs['instance']

    obj_choice = f"{obj_instance.department.hospital.name} - {obj_instance.department.name}"

    for choice_id, choice_str in self.fields['hosp_depart'].choices:
      if choice_str == obj_choice:
        self.initial['hosp_depart'] = choice_id
        break

  # List available hospital choices from the database
  hosp_depart = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Department.objects.all())


# Custom choice field to change the displayed labels for the hospitals
class HospitalChoiceField(forms.ModelChoiceField):
  def label_from_instance(self, hospital_obj):
    return hospital_obj.name


# Custom choice field to change the displayed labels for the configs
class ConfigChoiceField(forms.ModelChoiceField):
  def label_from_instance(self, config_obj):
    return config_obj.id


class EditDepartmentForm(forms.ModelForm):
  class Meta:
    model = models.Department
    fields = [
      'name',
      'hospital',
      'config',
    ]

    labels = {
      'name': 'Navn',
    }

  hospital = HospitalChoiceField(queryset=models.Hospital.objects.all(), label="Hospital")
  config = ConfigChoiceField(queryset=models.Config.objects.all(), label="Konfiguration")


class EditConfigForm(forms.ModelForm):
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
      'pacs_calling',
    ]


class EditProcedureForm(forms.ModelForm):
  class Meta:
    model = models.ProcedureType
    fields = [
      'type_name'
    ]

class EditHospitalForm(forms.ModelForm):
  class Meta:
    model = models.Hospital
    fields = [
      'name',
      'short_name',
      'address',
    ]


class EditHandledExaminationsForm(forms.ModelForm):
  class Meta:
    model = models.HandledExaminations
    fields =[
      'accession_number'
    ]
# --- EDIT FORMS END --- #


# --- ADD FORMS START --- #
class AddUserForm(forms.ModelForm):
  class Meta:
    model = models.User
    fields = [
      'username',
      'password',
    ]

    labels = {
      'username': 'Brugernavn'
    }

    widgets = {
      'password': forms.PasswordInput(),
    }

  confirm_pass = forms.CharField(max_length=120, label="Gentag password", widget=forms.PasswordInput())

  # List available hospital choices from the database
  hosp_depart = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Department.objects.all())

  # List available user groups
  user_group = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.UserGroup.objects.all())


class AddHospitalForm(forms.ModelForm):
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

  def __init__(self, *args, **kwargs):
    # Change the id attribute of the HTML field element, as to avoid naming
    # conflict with the AddDepartmentForm, which also contains a name field.
    super(AddHospitalForm, self).__init__(*args, **kwargs)
    self.fields['name'].widget = forms.TextInput(attrs={
      'id': 'id_hospital_name',
    })


class AddDepartmentForm(forms.ModelForm):
  class Meta:
    model = models.Department
    fields = [
      'name',
    ]

    labels =  {
      'name': 'Navn',
    }

  # List available hospitals
  hospital = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Hospital.objects.all())


class AddProcedureForm(forms.ModelForm):
  class Meta:
    model = models.ProcedureType

    fields = [
      'type_name',
    ]

    labels = {
      'type_name' : 'Procedure Navn',
    }

class AddConfigForm(forms.ModelForm):
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


class AddHandledExaminationsForm(forms.ModelForm):
  class Meta:
    model = models.HandledExaminations
    fields = [
      'accession_number'
    ]


class AddProcedureMapping(forms.ModelForm):
  class Meta:
    model = models.Config.accepted_procedures.through
  
    fields = [
      'department',
      'proceduretype_id'
    ]

  department = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Department.objects.all())
  proceduretype_id = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.ProcedureType.objects.all())

# --- ADD FORMS END --- #


class GetBackupDateForm(forms.Form):
  dateofmessurement = forms.DateField(label='Backup fra dato (DD-MM-ÅÅÅÅ)', required=False)
