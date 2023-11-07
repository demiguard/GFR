from django import forms

import main_page.models as models
from main_page.libs.enums import GENDER_NAMINGS

class EditUserForm(forms.ModelForm):
  class Meta:
    model = models.User
    fields = [
      "username"
    ]

  def __init__(self, *args, **kwargs):
    # Call the base class to allow the form to be constructed using templating
    # This allows for access to self.fields
    super(EditUserForm, self).__init__(*args, **kwargs)

    # Get object instance this form is instantiated with
    obj_instance = kwargs['instance']

    self.initial['department'] = obj_instance.department
    self.initial['user_group'] = obj_instance.user_group

  # List available hospital choices from the database
  department   = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.Department.objects.all())
  user_group   = forms.ModelChoiceField(required=True, widget=forms.Select, queryset=models.UserGroup.objects.all())

# Custom choice field to change the displayed labels for the hospitals
class HospitalChoiceField(forms.ModelChoiceField):
  def label_from_instance(self, hospital_obj):
    return hospital_obj.name


# Custom choice field to change the displayed labels for the configs
class ConfigChoiceField(forms.ModelChoiceField):
  def label_from_instance(self, config_obj):
    return config_obj.id


class AddressChocieField(forms.ModelChoiceField):
  def label_from_instance(self, Address_obj):
    return Address_obj.id

class EditDepartmentForm(forms.ModelForm):
  class Meta:
    model = models.Department
    fields = [
      'name',
      'hospital',
      'config',
      'ldapPath'
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
      'ris_calling',
      'black_list'
    ]

  ris  = AddressChocieField(queryset=models.Address.objects.all(), label="RIS")
  pacs = AddressChocieField(queryset=models.Address.objects.all(), label="PACS")
  storage = AddressChocieField(queryset=models.Address.objects.all(), label="Storage")

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

#Note that the datefield is not editabled
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

