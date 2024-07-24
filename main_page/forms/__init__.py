# Python standard library
from datetime import datetime
from typing import Optional

# Third party Packages
from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList

# Clairvoyance Modules
from main_page.libs.enums import GENDER_NAMINGS
from main_page.models import GFRStudy, GFRMethods

class FillStudyForm(forms.Form):
  class Meta:
    widgets = {

    }

  #init
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]
  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]

  #Fields
  birthdate           = forms.DateField(label='Fødselsdato (DD-MM-ÅÅÅÅ)', required=False)
  cpr                 = forms.CharField(label='CPR', required=False)
  height              = forms.FloatField(label='Højde (cm)', required=False, localize=True)
  injection_time      = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date      = forms.DateField(label='Injektionsdato (DD-MM-ÅÅÅÅ)', required=False)
  name                = forms.CharField(label='Navn', required=False)
  sex                 = forms.ChoiceField(choices=sex_options, label='Køn', required=False)
  standcount          = forms.FloatField(label="Standardtælletal", required=False, localize=True)
  study_type          = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())
  thin_fac            = forms.FloatField(label='Fortyndingsfaktor', required=False)
  vial_number         = forms.IntegerField(label="Sprøjte nr.", min_value=0, max_value=99, required=False)
  vial_weight_after   = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, localize=True)
  vial_weight_before  = forms.FloatField(label='Sprøjtevægt før injektion (g)', required=False, localize=True)
  weight              = forms.FloatField(label='Vægt (kg)', required=False, localize=True)
  comment_field       = forms.CharField(label="Kommentar",
                                        required=False,
                                        widget=forms.Textarea(attrs={
                                          "style": "height:75px;",
                                          "class": "col-md-8"
                                          })
                                        )

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['cpr'].widget.attrs['readonly'] = True
    self.fields['name'].widget.attrs['readonly'] = True

    for field in self.fields:
      if field not in ['study_type']:
        self.fields[field].widget.attrs['class'] = 'form-control'


class GFRStudyForm(forms.ModelForm):
  class Meta:
    model = GFRStudy
    fields = [
      'PatientID',
      'PatientName',
      'PatientSex',
      'PatientBirthDate',
      'PatientHeightCM',
      'PatientWeightKg',
      'Standard',
      'ThinningFactor',
      'VialNumber',
      'InjectionWeightBefore',
      'InjectionWeightAfter',
      'Comment',
    ]
    localized_fields = [
      'PatientHeightCM',
      'PatientWeightKg',
      'InjectionWeightBefore',
      'InjectionWeightAfter',
      'PatientBirthDate',
    ]
    labels = {
      'PatientID' : "CPR",
      'PatientName' : "Navn",
      'PatientSex' : "Køn",
      'PatientBirthDate' : "Fødseldag (DD-MM-ÅÅÅÅ)",
      'PatientHeightCM' : "Højde (cm)",
      'PatientWeightKg' : "Vægt (kg)",
      'VialNumber' : "Hætteglas nr.",
      'InjectionWeightBefore' : "Sprøjtevægt før injektion (g)",
      'InjectionWeightAfter' : "Sprøjtevægt efter injektion (g)",
      'Standard' : "Standardtælletal",
      'ThinningFactor' : "Fortyndingsfaktor",
      'Comment' : "Kommentar",
    }
    widgets = {

    }

  PatientBirthDate = forms.DateField(input_formats=[
                                    '%d-%m-%Y',
                                    '%d/%m/%Y',
                                    '%Y-%m-%d',
                                    '%Y/%m/%d',
                                  ],
                                  label="Fødseldag",
                                  localize=True,
                                  required=True,
                                  widget=forms.DateInput(attrs={'type' : 'date'}, format="%d/%m/%Y"))

  InjectionTime = forms.TimeField(label="Injektionstidspunkt (tt:mm)",
                                  localize=True,
                                  required=False)

  InjectionDate = forms.DateField(input_formats=[
                                    '%d-%m-%Y',
                                    '%d/%m/%Y',
                                    '%Y-%m-%d',
                                    '%Y/%m/%d',
                                  ],
                                  label="Injektionsdato",
                                  localize=True,
                                  required=False, widget=forms.DateInput({'type' : 'date', "pattern" : "dd-mm-yyyy", 'min' : "1900-01-01", 'max' : "2099-12-31" }, format="%d/%m/%Y"))

  Method = forms.ChoiceField(choices=GFRMethods.form_choices,
                             widget=forms.RadioSelect,
                             required=False)

  def __init__(self, *args, **kwargs):
    instance: Optional[GFRStudy] = kwargs.get('instance')

    if instance:
      if instance.InjectionDateTime is not None:
        instance['InjectionTime'] = instance.InjectionDateTime.time()
        instance['InjectionDate'] = instance.InjectionDateTime.date()

    super().__init__(*args, **kwargs)

    self.fields['PatientID'].widget.attrs['readonly'] = True
    self.fields['PatientName'].widget.attrs['readonly'] = True

    for field in self.fields:
      if field not in ['Method']:
        self.fields[field].widget.attrs['class'] = 'form-control'


  def save(self, commit=True):
    form: GFRStudy = super(GFRStudyForm, self).save(commit=False)

    if self.cleaned_data['InjectionTime'] is not None and \
       self.cleaned_data['InjectionDate'] is not None:

      form.InjectionDateTime = datetime.combine(
        self.cleaned_data['InjectionDate'],
        self.cleaned_data['InjectionTime']
      )

    if commit:
      form.save()
    return form
