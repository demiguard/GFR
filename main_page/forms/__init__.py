# Python standard library
from datetime import datetime
from typing import Optional

# Third party Packages
from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.utils.timezone import get_current_timezone
from django.forms.utils import ErrorList

# Clairvoyance Modules
from main_page.forms.fields import DanishDateField, DanishFloatField, SecondLessTimeField
from main_page.libs.enums import GENDER_NAMINGS
from main_page.models import GFRStudy, GFRMethods, InjectionSample

class SampleForm(forms.ModelForm):
  class Meta:
    model = InjectionSample
    fields = [
      'DateTime',
      'CountPerMinutes',
      'DeviationPercentage'
    ]

  SampleTime = SecondLessTimeField(label="Injektionstidspunkt (tt:mm)",
                                  localize=True,
                                  required=False)

  SampleDate = DanishDateField(label="Injektionsdato",
                                  localize=True,
                                  required=False)

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)

    for field in self.fields:
      self.fields[field].widget.attrs['class'] = 'form-control'

class GFRStudyForm(forms.ModelForm):
  class Meta:
    model = GFRStudy
    fields = [
      'PatientID',
      'PatientName',
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
    field_classes = {
      'PatientHeightCM' : DanishFloatField,
      'PatientWeightKg' : DanishFloatField,
      'Standard' : DanishFloatField,
      'InjectionWeightBefore' : DanishFloatField,
      'InjectionWeightAfter' : DanishFloatField,
      'ThinningFactor' : DanishFloatField,
    }

  PatientSex = forms.ChoiceField(
    choices=[(i, gender) for i, gender in enumerate(GENDER_NAMINGS)],
    label="Køn"
  )

  PatientBirthDate = DanishDateField(label="Fødseldag",
                                  localize=True,
                                  required=True)

  InjectionTime = SecondLessTimeField(label="Injektionstidspunkt (tt:mm)",
                                  localize=True,
                                  required=False)

  InjectionDate = DanishDateField(label="Injektionsdato",
                                  localize=True,
                                  required=False)

  Method = forms.ChoiceField(choices=GFRMethods.form_choices,
                             widget=forms.RadioSelect,
                             required=False)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    instance: Optional[GFRStudy] = kwargs.get('instance')

    if isinstance(instance, GFRStudy):
      if instance.InjectionDateTime is not None:
        self.fields['InjectionTime'].initial = instance.InjectionDateTime.astimezone(get_current_timezone()).time()
        self.fields['InjectionDate'].initial = instance.InjectionDateTime.date()

    self.fields['PatientID'].widget.attrs['readonly'] = True
    self.fields['PatientName'].widget.attrs['readonly'] = True

    for field in self.fields:
      if field not in ['Method']:
        self.fields[field].widget.attrs['class'] = 'form-control'
      elif isinstance(instance, GFRStudy) and field == 'Method':
        bound_field = self.fields['Method']
        if instance.GFRMethod is not None:
          bound_field.initial = GFRMethods(instance.GFRMethod)

  def save(self, commit=True):
    study: GFRStudy = super(GFRStudyForm, self).save(commit=False)

    if self.cleaned_data['InjectionTime'] is not None and \
       self.cleaned_data['InjectionDate'] is not None:

      study.InjectionDateTime = datetime.combine(
        self.cleaned_data['InjectionDate'],
        self.cleaned_data['InjectionTime'],
        tzinfo=get_current_timezone()
      )

    if self.cleaned_data['Method']:
      for option in GFRMethods:
        if option.value == self.cleaned_data['Method']:
          study.GFRMethod = option

    if commit:
      study.save()
    return study
