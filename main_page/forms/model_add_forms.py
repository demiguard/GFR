from django import forms

import main_page.models as models
from main_page.libs.enums import GENDER_NAMINGS

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
  user_group = forms.ChoiceField(required=True, widget=forms.Select, choices=models.UserGroup.choices)

  def clean(self):
    cleaned_data = super().clean()
    password = cleaned_data.get('password')
    confirm_pass = cleaned_data.get('confirm_pass')

    if password and confirm_pass and password != confirm_pass:
      self.add_error('confirm_pass', "Adgangskoderne matcher ikke.")

    return cleaned_data
  
  def save(self, commit=True):
    user = super().save(commit=False)

    # Handle additional fields
    department = self.cleaned_data['hosp_depart']
    group = self.cleaned_data['user_group']

    user.department = department
    user.user_group = group

    if commit:
        user.save()
        
    return user



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

  def save(self, commit=True):
    department = super().save(commit=False)

    hospital = self.cleaned_data['hospital']
    config = self.cleaned_data['config']

    # Handle additional fields
    department.hospital = hospital 
    department.config = config

    if commit:
      department.save()

    return department


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
      'ris_calling',
      'black_list'
    ]

  ris  = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Address.objects.all())
  pacs = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Address.objects.all())

  def save(self, commit=True):
    config = super().save(commit=False)

    ris = self.cleaned_data['ris']
    pacs = self.cleaned_data['pcas']

    # Handle additional fields
    config.ris = ris 
    config.pacs = pacs

    if commit:
      config.save()

    return config

#Note that the datefield is added automatic
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

  def save(self, commit=True):
    procedure = super().save(commit=False)

    department = self.cleaned_data['department']
    typeId = self.cleaned_data['proceduretype_id']

    # Handle additional fields
    procedure.department = department 
    procedure.proceduretype_id = typeId

    if commit:
      procedure.save()

    return procedure
  

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
