from django import forms

import main_page.models as models
from main_page.libs.enums import GENDER_NAMINGS

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

