from django import forms
from django.core.validators import RegexValidator

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
  rigs_nr = forms.CharField(label='Accession nummer')

class ControlPatient1(forms.Form):
  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]

  cpr       = forms.CharField(label='Cpr-nr.',        required=False )
  name      = forms.CharField(label='Navn',           required=False )
  sex       = forms.ChoiceField(label='Køn', choices=sex_options,  required=False, disabled=True)
  birthdate = forms.DateField(label='Fødseldato',     required=False)

  cpr_confirm       = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")  
  name_confirm      = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  sex_confirm       = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  birthdate_confirm = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")


  def __init__(self, *args, **kwargs):
    super(ControlPatient1, self).__init__(*args, **kwargs)
    self.fields['cpr'].widget.attrs['readonly']       = True
    self.fields['name'].widget.attrs['readonly']      = True
    self.fields['sex'].widget.attrs['readonly']       = True    
    self.fields['birthdate'].widget.attrs['readonly'] = True

class ControlPatient2(forms.Form):
  height = forms.CharField(label='Højde (cm)',  widget=forms.TextInput(attrs={'class' : "col-md-12"}))
  weight = forms.CharField(label='Vægt (kg)',   widget=forms.TextInput(attrs={'class' : "col-md-12"}))


  height_confirm = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  weight_confirm = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")

  def __init__(self, *args, **kwargs):
    super(ControlPatient2, self).__init__(*args, **kwargs)
    self.fields['height'].widget.attrs['readonly'] = True
    self.fields['weight'].widget.attrs['readonly'] = True

class ControlPatient3(forms.Form):
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før injektion (g)', required=False, widget=forms.TextInput(attrs={'class' : "col-md-12"}))  
  vial_weight_after  = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, widget=forms.TextInput(attrs={'class' : "col-md-12"}))
  injection_time     = forms.TimeField(label='Injektionstidspunkt', required=False)
  injection_date     = forms.DateField(label='InjektionsDato',      required=False, input_formats=['%d-%m-%Y'])

  vial_weight_before_confirm = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  vial_weight_after_confirm  = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")  
  injection_time_confirm     = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  injection_date_confirm     = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
# 
  def __init__(self, *args, **kwargs):
    super(ControlPatient3, self).__init__( *args, **kwargs)
    self.fields['vial_weight_before'].widget.attrs['readonly'] = True
    self.fields['vial_weight_after'].widget.attrs['readonly'] = True
    self.fields['injection_time'].widget.attrs['readonly'] = True
    self.fields['injection_date'].widget.attrs['readonly'] = True    

class ControlPatient4(forms.Form):
  
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]

  thin_fac   = forms.IntegerField(label='Fortyndingsfaktor', required=False, widget=forms.TextInput(attrs={'class' : "", 'step': '1'}))
  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect(), disabled=True)  

  thin_fac_confirm   = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  study_type_confirm = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")

  def __init__(self, *args, **kwargs):
    super(ControlPatient4, self).__init__(*args, **kwargs)
    self.fields['thin_fac'].widget.attrs['readonly']   = True
    self.fields['study_type'].widget.attrs['readonly'] = True
  
class ControlPatient5(forms.Form):
  stdCnt = forms.DecimalField(label='Standardtælletal', max_digits=1 , required=False, widget=forms.TextInput(attrs={'class' : "col-md-5"}))

  stdCnt_confirm = forms.BooleanField(required=False, label="")

  def __init__(self, *args, **kwargs):
    super(ControlPatient5, self).__init__( *args, **kwargs)
    self.fields['stdCnt'].widget.attrs['readonly'] = True
    self.fields['stdCnt'].widget.attrs['class'] = 'form-input'
    self.fields['stdCnt_confirm'].widget.attrs['class'] = 'confirm-row-checkbox'    

class ControlPatient6(forms.Form):
  sample_time = forms.TimeField(label='Dato',  required=False)
  sample_date = forms.DateField(label='Tidpunkt',  required=False, input_formats=['%d-%m-%Y'])
  sample_cnt  = forms.FloatField(label='Tælletal', required=False, widget=forms.TextInput(attrs={'class' : "sample_count"}))

  sample_confirm = forms.BooleanField(required=False, label='')

  def __init__(self, *args, **kwargs):
    super(ControlPatient6, self).__init__( *args, **kwargs)
    self.fields['sample_time'].widget.attrs['readonly'] = True    
    self.fields['sample_date'].widget.attrs['readonly'] = True  
    self.fields['sample_cnt' ].widget.attrs['readonly'] = True
    self.fields['sample_time'].widget.attrs['class']    = 'form-input'    
    self.fields['sample_date'].widget.attrs['class']    = 'form-input'
    self.fields['sample_cnt'].widget.attrs['class']     = 'form-input sample_count'
    self.fields['sample_confirm'].widget.attrs['class'] = 'confirm-row-checkbox' 

class ControlPatientConfirm(forms.Form):
  bamID = forms.CharField(label='Bam ID', max_length=8, required=False, widget=forms.TextInput(attrs={'class' : "col-md-3"}))

class Fillpatient_1(forms.Form):
  cpr = forms.CharField(label='Cpr-nr.',  required=False)
  name = forms.CharField(label='Navn',    required=False)

  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]
  sex = forms.ChoiceField(choices=sex_options, label='Køn', required=False)
  
  birthdate = forms.DateField(label='Fødselsdato (DD-MM-ÅÅÅÅ)', required=False)

  def __init__(self, *args, **kwargs):
    super(Fillpatient_1, self).__init__(*args, **kwargs)
    self.fields['cpr'].widget.attrs['readonly'] = True
    self.fields['name'].widget.attrs['readonly'] = True


class Fillpatient_2(forms.Form):
  height = forms.CharField(
    label='Højde (cm)',
    required=False,
    validators=[
      RegexValidator(
        regex='^[0-9]+(\,[0-9]+)?$',
        message='Feltet skal bestå af 0-9 og max 1 ,'
      )
    ])

  weight = forms.CharField(
    label='Vægt (kg)',
    required=False,
    validators=[
      RegexValidator(
        regex='^[0-9]+(\,[0-9]+)?$',
        message='Feltet skal bestå af 0-9 og max 1 ,'
      )
    ]
  )


class Fillexamination(forms.Form):
  vial_weight_before = forms.CharField(label='Sprøjtevægt før injektion (g)', required=False)
  vial_weight_after = forms.CharField(label='Sprøjtevægt efter injektion (g)', required=False)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (DD-MM-ÅÅÅÅ)', required=False)  


class Filldosis(forms.Form):
  #std_cnt = forms.IntegerField(label='Standard tælletal', required=False, min_value=0)
  thin_fac = forms.CharField(label='Fortyndingsfaktor', required=False)
  save_fac = forms.BooleanField(required=False, label='Gem')


class FillStudyType(forms.Form):
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())


class FillStudyTest(forms.Form):
  study_time = forms.TimeField(label='Blodprøve taget kl:', required=False)
  study_date = forms.DateField(label='Blodprøve taget dato', required=False)

  def __init__(self, *args, **kwargs):
    super(FillStudyTest, self).__init__(*args, **kwargs)

    # Add bootstrap class to fields
    for _, field in self.fields.items():
      field.widget.attrs['class'] = 'form-control'


class SearchForm(forms.Form):
  name = forms.CharField(label='Navn', required=False)
  cpr  = forms.CharField(label='Cpr-nr.', required=False)
  accession_number = forms.CharField(label='Accession nummer', required=False)
  from_date = forms.DateField(label='Fra dato (DD-MM-ÅÅÅÅ)', required=False)
  to_date = forms.DateField(label='Til dato (DD-MM-ÅÅÅÅ)', required=False)

  def __init__(self, *args, **kwargs):
    super(SearchForm, self).__init__(*args, **kwargs)

    # Add bootstrap class to fields
    for _, field in self.fields.items():
      field.widget.attrs['class'] = 'form-control'

#This form is intented just to be one form containing all the other forms for fill study
#Note that this cannot contain Fillstudy Test, since there may be multiple Tests
class FillStudyGrandForm(forms.Form):
  #init
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]
  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]
  
  #Fields
  bamID = forms.CharField(label='Bam ID', max_length=8, required=False, widget=forms.TextInput(attrs={'class' : "col-md-3"}))
  birthdate = forms.DateField(label='Fødselsdato (DD-MM-ÅÅÅÅ)', required=False)
  cpr  = forms.CharField(label='Navn', required=False)
  height = forms.CharField( label='Højde (cm)', required=False)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (DD-MM-ÅÅÅÅ)', required=False)  
  name = forms.CharField(label='Navn', required=False)
  save_fac = forms.BooleanField(required=False, label='Gem')
  sex = forms.ChoiceField(choices=sex_options, label='Køn', required=False)
  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())
  thin_fac = forms.CharField(label='Fortyndingsfaktor', required=False)
  vial_weight_after = forms.CharField(label='Sprøjtevægt efter injektion (g)', required=False)
  vial_weight_before = forms.CharField(label='Sprøjtevægt før injektion (g)', required=False)
  weight = forms.CharField( label='Vægt (kg)', required=False)

  def __init__(self, *args, **kwargs):
    super(FillStudyGrandForm, self).__init__(*args, **kwargs)


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
    fields = [
      'accession_number'
    ]

class EditAddressForm(forms.ModelForm):
  class Meta:
    model = models.Address
    fields = [
      'ae_title',
      'ip',
      'port',
      'description'
    ]

class EditServerConfigurationForm(forms.ModelForm):
  class Meta:
    model = models.ServerConfiguration
    fields = [
      'samba_ip',
      'samba_name',
      'samba_user',
      'samba_pass',
      'samba_pc',
      'samba_share',
      'AE_title'
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
  config = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Config.objects.all())


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

class AddAddressForm(forms.ModelForm):
  class Meta:
    model = models.Address
    fields = [
      'ae_title',
      'ip',
      'port',
      'description'
    ]

class AddServerConfigurationForm(forms.ModelForm):
  class Meta:
    model = models.ServerConfiguration
    fields = [
      'samba_ip',
      'samba_name',
      'samba_user',
      'samba_pass',
      'samba_pc',
      'samba_share',
      'AE_title'
    ]

# --- ADD FORMS END --- #


class GetBackupDateForm(forms.Form):
  dateofmessurement = forms.DateField(label='Backup fra dato (DD-MM-ÅÅÅÅ)', required=False)

class NukeListStudiesForm(forms.Form):
  l_hospital = forms.ModelChoiceField(label='Hospital', required=True, widget=forms.Select, queryset=models.Hospital.objects.all().values_list('short_name', flat=True))
  l_bamID = forms.CharField(label='Bam ID', max_length=8, required=True, widget=forms.TextInput(attrs={'class' : "col-md-3"}))

class NukeDeletedStudiesForm(forms.Form):
  d_hospital = forms.ModelChoiceField(label='Hospital', required=True, widget=forms.Select, queryset=models.Hospital.objects.all().values_list('short_name', flat=True))
  d_bamID = forms.CharField(label='Bam ID', max_length=8, required=True, widget=forms.TextInput(attrs={'class' : "col-md-3"}))
